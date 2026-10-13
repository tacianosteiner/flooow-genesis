# Room V2 — history writer startup and producer integration

Date: 2026-10-13. Branch `feature/room-v2-executive-product-evolution`; baseline `3d69406140379783056004bebe631790ac7a77ff`. Successor to [identity/ACL qualification](ROOM-V2-production-identity-acl-cutover-qualification.md).

**CODE READY. NOT ACTIVATED. NO NUMBERED MIGRATION. NO PRODUCTION MANIFEST. NO SHARED DB. NO ROOM OPERATIONAL AUTHORITY.**

## Producer and checkpoint contract

The existing processor reads the sales-intelligence checkpoint, obtains a strictly ordered organization-scoped batch, materializes each change and advances one CAS checkpoint to the batch's final trigger only after every materialization succeeds. Legacy mode first reads current projection and treats an already-covered trigger as complete; otherwise it reads current authoritative evidence, captures membership, assembles/calculates, finalizes one snapshot/record and calls the projection-only writer. That unchanged path remains the normal API composition.

Historical mode adds the application port `MarketplaceSalesIntelligenceHistoryPublication`; it has no JDBC/PostgreSQL types. The existing five publication outcomes moved to the application layer, rather than creating a second mapping vocabulary. The processor directly passes the exact finalized snapshot and record to this port. The observer remains test instrumentation; it performs no persistence in production wiring. A domain test asserts object identity between observed and submitted snapshot, one evidence read/calculation, and no legacy projection writes.

Historical processing reconciles the genuine publication key before reading evidence or running current policy. Exact stored publication returns IdenticalPublished; a later current winner must have valid source scope/boundary, frozen manifest/receipt and current linkage. Unlinked legacy current rows cannot supply historical Superseded completion. If absent, one attempt reads evidence and constructs its frozen pair exactly once. No projection-only write precedes or follows historical publication.

| Outcome | Processor/checkpoint behavior |
|---|---|
| Published | Known committed publication; materialization complete |
| IdenticalPublished | Exact durable retry; complete without new calculation/time |
| Superseded with non-null revision | Independently reconcile the winner; complete only on Known |
| Superseded with legacy NULL revision | Failure; no historical completion invented |
| IntegrityFailure | No checkpoint advancement; a known unsuccessful submission does not retain an uncertain commit claim |
| CommitOutcomeUnknown or exception after submission | Preserve frozen pair; ReconciliationRequired; checkpoint unchanged |

The processor retains at most one uncertain input, including its original change, and serializes calls on the same instance. Separate instances remain subject to native subject locks and checkpoint CAS. Retry compares the retained expected canonical bytes/digest when present. An exact committed row resolves the hold; divergent same-key context fails closed; absence allows resubmission of the same pair. After restart, independently validated stored publication is reused without reconstructing historical outcomes. A checkpoint already advanced by another matched worker does not discard a surviving uncertain input: it is reconciled first.

Checkpoint granularity remains **whole batch**, not per change. N1/N2 durable and N3 unknown leaves the prior batch checkpoint unchanged. Restart resolves N1/N2 from stored publications and resumes N3. Publication/current/receipt are one SQL transaction; checkpoint advancement is a subsequent transaction. This is a durable-publication-before-checkpoint protocol with exact replay, **not** a claim that checkpoint and history share one transaction. A committed publication may legitimately precede its checkpoint.

Live pipeline handles ReconciliationRequired as a blocked projection phase, using the existing safe block vocabulary. No exception, integrity failure or uncertainty becomes completion or execution authority.

## Startup engine and matching factory

`RoomHistoryWriterStartupGuard` checks a supplied immutable `RoomHistoryStartupManifest` on one read-only REPEATABLE READ connection. Expected rows are copied defensively; the engine never constructs expectations from the target's observed rows. It compares the full ordered Flyway history: version/type/script/checksum/success/description, with no future-version cap or ignored entry.

Catalog sections cover seven tables including V018; all their columns/defaults/nullability/identity; PK/UK/FK and complete CHECK definitions; six protected function signatures, owners, language/security/volatility/strictness/defaults/variadic/parallel/search-path/result and SHA-256 of stored body; 26 application triggers and FK enforcement triggers; identity owner/min/max/increment/cycle/privileges; runtime and owner's exact source-column permissions; PUBLIC/unexpected/grant-option permissions; protected schema/database ownership and CREATE/USAGE; role attributes and all memberships involving owner/runtime. Extra protected function overloads/names are included. Disabled internal RI triggers are checked using stable constraint/function/event metadata, not generated OID-based names.

Function body provenance hashes `prosrc` after CRLF→LF only. Owner, signature and security/search-path are separate checks. This is exact body provenance for the qualified PostgreSQL 18 representation, not a migration-file SHA or a claim that `pg_get_functiondef` equals source file formatting. CHECK/FK text uses PostgreSQL's catalog rendering in the immutable qualification representation; incompatible rendering fails closed rather than being normalized permissively.

Statuses: READY, NOT_CONFIGURED, MIGRATION_HISTORY_MISMATCH, SCHEMA_MISMATCH, OWNER_MISMATCH, ACL_MISMATCH, FUNCTION_MISMATCH, TRIGGER_MISMATCH, RUNTIME_IDENTITY_MISMATCH, UNAVAILABLE. They expose no credentials, SQL exception details or economic truth.

`RoomHistoryWriterCompositionFactory.create` composes the real repository and historical processor only after READY. Blocked results contain no processor and start no checkpoint loop. There is no legacy fallback, environment switch or call from normal Application.kt. Production verification requires an explicit legitimate historical migration anchor in its complete release manifest; the known Package V043 cannot be that Room anchor. No Room version/checksum is assigned here.

## Qualification artifact provenance and production separation

The committed `history_guard_qualification_manifest.json` is a **TEST-ONLY synthetic qualification representation**: genuine V001–V042 source checksums plus source-hash markers for the unnumbered candidate/ACL overlay and exact catalog expectations. Baseline CRC32 values are calculated from repository SQL lines using Flyway's line-oriented checksum representation and matched against actual history. No fake V043/V044 row is installed.

Fixture authoring used a separate pristine disposable reference compilation of the reviewed DDL to fix PostgreSQL-normalized catalog forms, followed by source-derived updates for the explicitly reviewed ACL/metadata contract. Those bytes are frozen in source before target/adversarial campaigns. The authoring/export method is absent from committed tests and runtime. Qualification tests load the immutable file and verify its candidate/ACL source hashes; they never regenerate expected rows from the system under test or adopt mutated target metadata. This fixture is not a production release manifest or authority to migrate.

Only package-internal qualification entrypoints accept this marked representation. Public production verification rejects it, an absent manifest, or a manifest without its legitimate Room migration anchor. Relabeling the baseline profile as production does not authorize startup. A future release must independently freeze its actual final numbered migration/checksum/catalog contract; this task cannot supply it.

The ACL overlay now adds only the actual feed/checkpoint/guard needs: runtime journal update_id/change_kind SELECT; organization_id SELECT for organization existence/pending enumeration; checkpoint SELECT/INSERT and last_change_sequence UPDATE; seven Flyway history SELECT columns. Owner's journal read remains the original four metadata columns. Owner/runtime receive explicit protected-schema USAGE, never CREATE. No raw source payload grant is added to the writer. Integrated tests inject an independently restricted read-only source fixture principal for the already-existing authoritative evidence repository; its source reads are separate from writer grants, and it has no production provisioning or write authority.

## Executed proof and adversarial findings

All PostgreSQL campaigns use fresh own `postgres:18.4` Testcontainers, inspected 127.0.0.1 port binding, canonical V001–V042 baseline and unnumbered candidate/ACL. Admin is used only for fixture creation, reference compilation and deliberate isolated mutation/restoration. Guard, publication and checkpoint operations use the restricted runtime; source reads use the separate non-superuser read-only fixture. No V043, shared/Package database, production credentials or live provider calls.

Executable compatibility matrix:

- OLD+OLD: genuine legacy publication before candidate succeeds.
- OLD+NEW: guard blocks before a processor is returned; historical writer also rejects absent schema.
- NEW+OLD: genuine legacy publication without revision linkage rejects; current diagnostic reads remain supported.
- NEW+NEW: qualification guard READY, matched factory returns processor, restricted publication/checkpoint/read succeeds.

Integrated cases prove unresolved→Ready/Incomplete and correction history through the actual producer/port/writer/checkpoint/reader; immutable prior manifests; no duplicate history after restart; exact retry and divergent reconciliation; native lost COMMIT acknowledgement; unknown-with-no-row frozen retry; actual precommit rollback; thrown submission HOLD; verified later winner without business recomputation; multi-order batch barrier and restart; concurrent matched instances with one publication; reconciliation of a held input after another worker advances the checkpoint.

Guard attacks independently change missing table, FK target, CHECK expression, application/internal trigger enablement, function body/security/search-path, owner, owner source privileges, runtime/owner membership, forbidden role attributes, runtime grants, PUBLIC/outsider table/function/schema grants, migration checksum/script/version/success or expected history entries. Every attack blocks startup; isolated cleanup restores the exact accepted contract. A table-level SELECT revoke also removes column grants in PostgreSQL: the fixture restores the explicit owner columns, rather than weakening the guard or keeping broad table access.

The preceding 26 lineage/ACL/cutover methods remain passing under the restricted role. Domain snapshot/record identity and result-mapping tests, API and affected live-pipeline regressions are included. Final counts/commands are recorded below after the closing campaign. Repeated runs/reference compilation are not counted as distinct qualification tests.

## Gate and integrity decision

PRODUCER_HISTORY_PUBLICATION_PORT_READY=YES. CHECKPOINT_RESULT_MAPPING_READY=YES. COMMIT_UNKNOWN_RECONCILIATION_READY=YES. SUPERSEDED_VERIFICATION_READY=YES. STARTUP_GUARD_ENGINE_READY=YES. SCHEMA_BINARY_COMPATIBILITY_EXECUTABLE_PROOF=YES. COMPOSITION_CODE_READY=YES. WRITER_COMPOSITION_TECHNICALLY_READY=YES.

COMPOSITION_ACTIVATED=NO. PRODUCTION_STARTUP_MANIFEST_READY=NO. ROOM_MIGRATION_SLOT_READY=NO. ROOM_MIGRATION_VERSION=NONE. PRODUCTION_SCHEMA_PROMOTION_READY=NO. ROOM_OPERATIONAL=NO; execution/recovery blocked; raw retrieval/API/UI absent.

One external blocker remains: Package V043 executable canonical promotion and fresh exclusive Room slot allocation, then the legitimate production migration/manifest and full-chain qualification. No unresolved Room HIGH/MEDIUM/LOW finding remains in this bounded code/qualification tranche. Deployed fleet exclusion and final release activation are future governed actions, not evidence manufactured from this lab.

## Closing validation

```powershell
.\gradlew.bat :applications:marketplace-operations:test :applications:marketplace-operations-persistence-postgres:test --tests '*PostgresMarketplaceSalesIntelligenceLineageTest' :applications:marketplace-operations-api:test :applications:marketplace-live-pipeline:test --console=plain
python scripts/room_lineage/verify_historical_blueprint.py --parser-path C:\Users\xmz_r\AppData\Local\Temp\room-lineage-sql-parser
git diff --check
```

Final campaign: BUILD SUCCESSFUL in 29 seconds; operations 531, PostgreSQL 38 (retained 26 plus five startup and seven integrated methods), API 69, affected live pipeline 13. Total 651 unique methods; zero failures, errors or skips. PostgreSQL aggregate time 24.956 seconds. Repeated focused runs and removed reference-authoring instrumentation are not additional tests. Static blueprint parsing/alignment passed for 41 base statements, six functions and 13 declared FKs; its NOT_PERFORMED label applies only to that static script, not the actual PostgreSQL campaign.

Validation scope is the source-frozen test-only form. It is not the absent numbered production form or canonical V001-through-future-Room chain. Main, Package and research remain unchanged; no numbered migration, default startup factory call, provider invocation, raw endpoint/UI or operational authority was added.
