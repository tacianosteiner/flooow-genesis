# SPEC-0091 — production schema promotion plan

Status: **bounded future plan; promotion HOLD; no version allocated**. Date: 2026-10-13. Governing [ADR-0091](../adr/ADR-0091-economic-projection-consumed-evidence-lineage.md); [coordination audit](../evidence/ROOM-V2-canonical-migration-release-coordination.md). This plan creates no migration, role, runtime mode, endpoint or execution authority.

## Gates and exact candidate boundary

HISTORICAL_PERSISTENCE_ENGINEERING_READY=YES from disposable PostgreSQL 18.4 proof. ROOM_SCHEMA_PROMOTION_TECHNICALLY_READY=NO until production identity/ACL and combined-history compatibility are qualified. ROOM_MIGRATION_SLOT_READY=NO. WRITER_COMPOSITION_READY=NO. PRODUCTION_SCHEMA_PROMOTION_READY=NO.

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
