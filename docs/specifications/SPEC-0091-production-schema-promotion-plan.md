# SPEC-0091 — production schema promotion plan

Status: **identity/ACL candidate qualified; production composition/promotion HOLD; no version allocated**. Date: 2026-10-13. Governing [ADR-0091](../adr/ADR-0091-economic-projection-consumed-evidence-lineage.md); [coordination audit](../evidence/ROOM-V2-canonical-migration-release-coordination.md). This plan creates no migration, production role, runtime mode, endpoint or execution authority.

## Gates and exact candidate boundary

HISTORICAL_PERSISTENCE_ENGINEERING_READY=YES from disposable PostgreSQL 18.4 proof. ROOM_SCHEMA_PROMOTION_TECHNICALLY_READY=YES for the reviewed base-plus-ACL candidate under separated identities; see the qualification amendment below. Full canonical-chain/client qualification awaits V043 and a final allocated migration. ROOM_MIGRATION_SLOT_READY=NO. WRITER_COMPOSITION_TECHNICALLY_READY=NO. WRITER_COMPOSITION_READY=NO. PRODUCTION_SCHEMA_PROMOTION_READY=NO.

The test-only resource matches the [accepted SQL blueprint](SPEC-0091-historical-lineage-ddl-blueprint.md): six historical tables, six functions, 26 triggers, 13 FKs and the V018 nullable current revision column/FK. Deferred validation, publication receipt, exact frozen payload/member/correction binding and immutable-history guards remain unchanged. Legacy rows retain NULL; no backfill or policy recomputation is authorized. All new accepted publications require a linked revision; legacy current rows are not permission to bypass that requirement. PostgreSQL 18.4 execution passed. No top-level transaction control, extension installation or concurrent index operation requires opting out of a transactional Flyway migration. The identity may consume sequence values on rollback; gaps are accepted, never repaired or used as evidence of publication.

Before conversion, bind the exact approved deployment identity and public schema ownership/search-path policy. Resolve existing V018/source ownership and the restricted runtime's needed SELECT, INSERT, UPDATE, scoped row-lock, identity sequence and exact function execution privileges. Validate invoker-trigger behavior under that identity. Do not give offline Package owners/service slots general Room privileges; do not deploy operational runtime as postgres merely to make tests pass. Candidate contains no role/ACL provisioning contract: that absence is an explicit promotion gap. Any needed owner/grant/search-path change requires a reviewed contract amendment and fresh candidate/blueprint alignment plus role-separated database tests; it is not a whitespace-only conversion.

A pure future test-marker removal is nonsemantic, but no version or production filename may be assigned before canonical eligibility. Once final production body is reviewed and numbered, freeze its source hash and actual Flyway checksum. Do not equate SHA-256 or working-copy line-ending bytes with Flyway CRC32. No changed applied checksum, repair, ignored failure, outOfOrder or cherryPick route is allowed.

## Ordered future release sequence — not executed

1. Package closes latest grouped SQL semantics, DML/concurrency/locks, installed crypto/ACL, integrated witness and complete fixture/runner obligations. Keep already-qualified structural/model facts intact. Production numeric policy provisioning and real field operation are separate later gates, not prerequisites invented for schema creation.
2. Package obtains exact governed isolated qualification scope and recorded implementation/review closure. Only its authorized process can produce an executable V043 successor and remove the fence. Qualify the final V001–V043 migration chain under its actual required deployment identity, restricted owners and installed crypto. Preserve V001–V042 checksums and all interlocks until legitimately closed.
3. Review and promote executable V043 into the canonical release path under repository governance. This plan performs no merge or deployment. A filename merged with the fence intact does not satisfy this step. Record exact resulting schema/history and deployed-state evidence; do not infer database state from branch state.
4. Fetch and re-audit main, Package, Room, all relevant migration inventories and any intervening reservations. Prove an exclusive next version and ordered canonical release. Only then allocate it in a new recorded decision; V044 is not promised today.
5. Close the Room production identity/ownership/ACL contract, matching history-client compatibility and trusted migration-runner configuration. Do not use ordinary flooow API startup to execute a postgres-only V043 chain. Package full-history/ACL readiness must be freshly independently approved for the changed database; do not copy observed manifests into authority.
6. Convert the approved candidate to the allocated production form, including only reviewed promotion amendments. In fresh loopback disposable PostgreSQL, execute full default ordered Flyway V001 through the new version without target-skipping V043, outOfOrder, cherryPick or failure suppression. Validate scripts/checksums/order/roles/ownership/effective ACLs. Prove upgrade from genuine V042 legacy rows, Package V043 baseline coexistence, deferred constraints and exact immutable lineage under the actual runtime identity. Do not report the existing target=042 test-only proof as this full-chain proof.
7. Implement the producer publication adapter/composition against the existing frozen snapshot and real writer. Current processor passes only a projection record to the legacy port; an observer hook is not a production publication seam. Preserve exact snapshot/record equality, both monotonic namespaces, one connection, duplicate/stale winner verification and checkpoint advancement only after durable known publication. Commit uncertainty holds/reconciles before checkpoint advance. New genuine triggers remain required; no invented policy-only event or historical reconstruction.
8. Run production-form atomic/idempotency/rollback/race/tenant/legacy/codec tests and API/runtime composition checks. Update fixture cleanup to avoid history TRUNCATE. Qualify old/new client-history boundaries and deny incompatible builds. Review schema and matching writer deployment artifacts together before release.
9. Enter controlled write exclusion: stop/drain every legacy sales materializer instance, wait for in-flight transactions and reconcile unknown commits/checkpoints. Prevent an old binary from restarting via autoscaling, health recovery or operator startup. Capture exact migration/current/checkpoint state and recovery evidence. Other paths touching affected rows must also be accounted for; a single process stop is not fleet exclusion.
10. With writer exclusion maintained, deploy/validate schema transactionally using the approved migration identity. Verify historical tables, V018 pointer column/FK, complete enabled triggers, actual migration checksum and expected ordered history/ACL state. No legacy writer resumes in this window. A failed migration keeps exclusion and composition disabled until exact transaction/history reconciliation.
11. Deploy only the matched history-aware composition while exclusion remains. Verify every instance uses it and no legacy write route remains. Release exclusion only after schema and startup/composition attestations pass. Perform a governed scoped publication/read verification before declaring historical persistence active. Do not turn Room operational, execution, recovery or retrieval on as a side effect.
12. Later raw evidence retrieval requires its own authorization, tenant security, redaction, API and UI qualification. Historical schema deployment provides no read-exposure authority.

## Writer composition gate

Every condition below must pass together; currently they do not:

- Production schema is migrated with exact matching checksum, history, ownership and runtime ACLs; all six tables, identity, boundary functions and enabled current/deferred/immutable triggers exist.
- The V018 nullable revision column and scoped FK are present; actual new transitions require revision linkage and database-owned receipts. Historical legacy NULL rows remain explicitly unlinked.
- Atomic writer and reader tests pass against the numbered production form under the real separated runtime identity, including source reads, row locks, identity allocation and validator invocation.
- The producer supplies the same frozen snapshot/record pair directly to publication; no public/environment observer hook is used. Retry and checkpoint behavior covers Published, IdenticalPublished, verified Superseded, IntegrityFailure and CommitOutcomeUnknown.
- Fleet write exclusion and matching-binary rollout are demonstrated. No old/new writer overlap, direct current projection bypass or mutable historical cleanup path remains. Schema triggers continue to reject bypass attempts.
- Full future history and ACL approvals are independently bound; old clients fail closed on extra migrations, compatible clients match exact versions/checksums without ignoring later rows.

## Transaction and deployment rollback limits

Transactional failure before migration commit can roll back DDL/data changes, subject to exact database/Flyway evidence; consumed sequence numbers are not rolled back. Do not claim a lost COMMIT acknowledgement means rollback. Reconcile schema history, catalog and publication key/context before retry or resuming writers.

Migration commit is not an automatically reversible application deployment. Once linkage triggers exist, rolling back the application to the projection-only writer causes rejected writes. Never disable triggers, drop history/pointers, erase receipts or rewrite applied migrations to make that rollback work. Maintain write exclusion, deploy a reviewed compatible forward fix, or perform separately governed restore/reconciliation preserving frozen history and source boundaries. Restoring a database also invokes Package incarnation/NOT_READY/requalification rules; it cannot resume prior authority implicitly. Normal application rollback alone is insufficient.

## Adversarial release dispositions

| Attack | Required denial/evidence |
|---|---|
| Remove V043 fence, merge gated filename, assume V044, insert a later-discovered lower version | Fence preserved; MODEL_A conditional; no version allocated until fresh exclusive inventory and canonical promotion |
| outOfOrder/cherryPick/ignore failures or partial target execution | Effective default ordered configuration checked; complete V001-through-new-version disposable proof; old target=38/042 tests excluded from this claim |
| Offline role, object, extension or ownership collision | Names have no direct new-object overlap; independently verify final catalog/roles/ACLs and required installed crypto, not just names |
| Checksum drift or runtime before schema | Freeze final checksum/source and ordered history; disabled composition/write exclusion until exact installed catalog matches |
| Legacy/new writer race or current pointer bypass | Drain all instances; matching rollout only; scoped root lock and DB pointer/receipt/immutability triggers reject bypass |
| Old client or stale Package history/ACL manifest | Old+new rejects; compatible exact client/independent reapproval required; no filtered history or observed-value adoption |
| Rollback after schema/publication commit | Exclusion plus compatible forward recovery or separately governed restore; no destructive down migration or old-writer restart |
| Accidental Package/main/research modification or raw read exposure | Intended Room documentation-only path audit, protected ref/worktree checks; no endpoint/UI/runtime changes |

This plan closes the sequencing decision, exposes production-specific gaps and defines executable acceptance criteria. It executes none of the future promotion steps.

## Qualified identity/ACL amendment

The earlier ownership/ACL gaps above are now closed as a disposable-tested contract, not a deployed state. Exact evidence and operation matrix: [identity/ACL qualification](../evidence/ROOM-V2-production-identity-acl-cutover-qualification.md). Production form is the base candidate plus the reviewed unnumbered ACL overlay, not the base SQL alone. Deployment is direct postgres; owner is flooow_room_history_owner NOLOGIN; writer and internal reconciliation reader use separately provisioned flooow_room_history_runtime. No Package role is reused. LOGIN secret provisioning is external, with restricted attributes/zero memberships independently verified.

The owner receives all six history tables, their identity sequence, six functions and V018 table ownership. Runtime receives exact header column INSERT excluding the identity, four detail table SELECT/INSERT, receipt SELECT, V018 SELECT/INSERT and nine mutable column UPDATEs, six bounded V015 SELECT column sets, subject currency UPDATE solely for row-lock eligibility, and one validator EXECUTE. Owner needs the same bounded source SELECT sets for deferred receipt validation. No source payload, receipt INSERT, identity sequence privileges, historical UPDATE/DELETE/TRUNCATE, schema CREATE, table TRIGGER, grant option or owner membership is authorized. Public CREATE and all six PUBLIC function EXECUTEs are removed. PUBLIC historical ACLs and unexpected existing grants must be rejected by production preflight; no default privilege assumption supplies authority.

All six functions use pg_catalog,public,pg_temp with protected public schema; five remain INVOKER and only the exact current-publication trigger is DEFINER to create its receipt. Runtime cannot directly execute/attach that trigger function. Writer/read transaction search paths are pinned too. Full restricted publication/rollback/race/read campaign and negative/catalog/shadowing tests passed. Runtime never runs as postgres and owns no historical object. New startup must not call general Flyway migrate as this restricted worker.

## Exact startup compatibility contract — implementation still gated

The future matching binary must carry a release-reviewed immutable manifest from source, never derive expected values from the connected database. Once allocation is legitimate, the manifest includes every ordered required migration version, SQL type, script filename and actual Flyway checksum through the new Room migration, including final executable V043. Until that artifact exists, production historical startup stays denied.

Before any processor/worker is composed, use one read-only snapshot to check:

1. Flyway history has exactly the approved required entries in increasing installed order, no missing/duplicate/failed/NULL/changed checksum/script/type or unapproved later version. Any compatible later release needs its own explicitly reviewed manifest; do not cap/filter away future history.
2. The six tables, generated identity, V018 column/FK, 13 FK targets, exact six function signatures/body provenance/security/search_path, 26 enabled triggers with expected timing/deferred attributes, owners and effective ACLs match the release manifest. Table existence alone never passes.
3. session_user=current_user is the approved restricted runtime; all forbidden role attributes/memberships/ownership/schema CREATE/grant options are absent. Public/untrusted operational roles have no protected-schema CREATE or historical access; no arbitrary role adoption. Required column/function privileges are exact.
4. Binary writer mode requires this historical contract, and its publication adapter consumes the exact frozen snapshot/record pair. No configured legacy materializer/current-row bypass is present. Missing history/ACL/schema returns NOT_READY and starts no writer or checkpoint loop; it does not fall back to legacy mode.

The current API has no such guard/composition and remains unchanged. Its sole production legacy constructor is Application.kt:270. Other legacy constructors are tests in the current-projection and lineage classes; all history constructors are in lineage tests. No CLI/scheduler/script alternate source construction was found. Exact client-history logic may reuse frozen-history verification patterns without copying the Package operational authority model. Its current provesV042 rejects future rows; update compatibility only in a matching reviewed release.

| Schema/binary | Proven behavior / release rule |
|---|---|
| OLD + OLD | Existing legacy publication works on V001–V042 |
| NEW + OLD | Genuine new projection-only publication rejects; old credentials must also be retired. This is DB/write fencing, not a retroactively installed old startup guard |
| OLD + NEW | Historical publication fails closed; future matching startup must deny before composing it |
| NEW + NEW | Restricted history-aware writer/read works on qualified candidate; production composition only after exact numbered-history guard qualification |

## Fleet exclusion state machine and reconciliation

No production orchestrator is created here. The governed deployment record must track these exact states/proofs; any missing/uncertain proof enters HOLD with writes excluded:

| State/transition | Required durable evidence |
|---|---|
| LEGACY_ACTIVE → DRAIN_REQUESTED | Enumerated every fleet instance/image, worker/schedule/operator/startup route; pause evidence materialization dispatch; record current organization checkpoint and V018 context; install restart/autoscale/health/operator exclusion |
| DRAIN_REQUESTED → LEGACY_DRAINED | Fence new legacy DB logins/credential reuse; drain/terminate existing tagged legacy sessions; independent pg_stat_activity/transaction inspection confirms none remain; stable repeated checkpoint/current reads and durable transaction receipts/logs reconcile every unknown acknowledgement |
| LEGACY_DRAINED → SCHEMA_MIGRATION_WINDOW | Approved schema/migration manifest, exact identity/preconditions and canonical slot; fleet exclusion still enforced; no legacy database sessions or write transactions |
| SCHEMA_MIGRATION_WINDOW → HISTORY_BINARY_DEPLOYING | Confirmed migration commit/history/checksum/catalog/ACL; unknown migration outcome holds, never infers rollback |
| HISTORY_BINARY_DEPLOYING → HISTORY_BINARY_VERIFIED | Every deployed instance is the matched digest, startup guard passed, no legacy construction/restart route, restricted credentials only; old credential remains retired |
| HISTORY_BINARY_VERIFIED → HISTORY_ACTIVE | Scoped known publication/read and checkpoint reconciliation pass; release exclusion only for matched history workers |
| Any uncertain transition → HOLD | Keep logins/routes/writers fenced; record exact gap; separately governed reconciliation before proceeding |

NOLOGIN alone leaves existing sessions alive: the disposable retirement test proves that fact and separately terminates its owned old backend before testing restart denial. Production cannot reuse that test as fleet proof. Retiring an identity shared with other services requires inventory and replacement credentials for legitimate unaffected users before its exclusion; it is not permission to disable a shared live role here. Do not rely on revoking CONNECT while PUBLIC still grants it, or on a process stop while restart routes remain enabled.

The current processor reads a checkpoint, handles ordered coalesced changes and advances its checkpoint only after successful materialization; its existing port recognizes Applied/NoOp/IntegrityFailure. Future adapter must map Published/IdenticalPublished/verified Superseded to known completion, IntegrityFailure to failure, and CommitOutcomeUnknown to HOLD/reconciliation before advancement. Never map uncertainty to success. Capture current trigger/read/policy/time/payload and authoritative V015 boundary without reconstructing legacy history. A stable consumer cursor is required while drained; providers need not stop canonical evidence ingestion. New genuine events after the captured cursor are processed after cutover, not skipped.

Resume from the reconciled checkpoint and legitimate current projection. Old NULL-linked rows stay unlinked. A later genuine trigger creates the first real revision; no backfill or regenerated historical policy outcome. Exact-key retry reuses frozen committed revision, not a new projectedAt; divergent candidate fails. Cursor leaps, guessed zero boundaries and mixed old/new writers are denied. Production-form processor/startup/fleet integration remains the single grouped Room HIGH gate; it is not installed by this contract task.
