# Room V2 — production identity, ACL and cutover qualification

Date: 2026-10-13. Branch `feature/room-v2-executive-product-evolution`; baseline `895ed16998d83885230523247ec05875af9943dc`. Successor to [release coordination](ROOM-V2-canonical-migration-release-coordination.md). Qualification scope is disposable PostgreSQL only; no production provisioning or normal writer composition.

## Existing identity inventory and evidence boundary

Audited compose, API Application.kt, CI, three datasource/Flyway connect paths, V001–V042 ownership/roles/grants/definer/locking patterns, controlled V029–V038 executor, offline frozen history client and read-only Package governance. Current compose runtime and startup migration user are `flooow`; the controlled historical executor also uses flooow. These are repository configuration facts, not a production identity recommendation. Docker's initialized POSTGRES_USER is a privileged bootstrap identity; its use in local compose does not prove production restriction.

V015/V018 owners are their migration creator; they have no explicit owner transfer. Public schema ownership/default ACLs depend on database initialization. Production owners, schema owner, default privileges and effective PUBLIC privileges are **UNOBSERVED**, because no shared database was contacted. PostgreSQL defaults grant function EXECUTE to PUBLIC; the candidate must explicitly revoke it. Existing V039–V042 restrict separate command/approval/verification capabilities and use bounded definer helpers; they do not grant general Room authority. Package V043 requires direct postgres and restricted NOLOGIN owners, but its owner/service identities are not reused and it was not executed.

The selected future Room migration identity is direct `postgres`, used only by separately governed deployment, to alter V018, create functions/tables/triggers/indexes, transfer ownership and install exact ACLs without adding another retained privileged login. This is a Room-specific decision, not inheritance of Package authority. Application connections must never use it. The test ACL body checks session_user/current_user before any ownership or grant action.

## Selected role model and ownership

| Purpose | Identity | Contract |
|---|---|---|
| Deployment | postgres | Direct trusted migration transaction; production execution remains unauthorized |
| Owner | flooow_room_history_owner | NOLOGIN, NOINHERIT, NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOREPLICATION, NOBYPASSRLS; zero memberships |
| Writer | flooow_room_history_runtime | Separately provisioned restricted login; same forbidden attributes and zero owner membership; secret supplied outside repository |
| Internal validated reader | flooow_room_history_runtime | Same worker identity because duplicate/commit reconciliation already needs complete validated historical reads; no extra login or API read authority |

The NOLOGIN owner owns all six historical tables, the generated identity sequence, all six functions and existing V018 projection table. Table ownership governs its column/FK/index/triggers; a trigger or altered column has no independent application-owner identity. Source V015 objects retain their baseline ownership. Transferring the revision table automatically transfers its owned identity sequence; catalogs prove that transfer. No runtime ownership, TRIGGER, schema CREATE or sequence privileges are granted.

Future schema-owned NOLOGIN role provisioning belongs in the reviewed migration/promotion contract; secret-bearing runtime LOGIN provisioning belongs in governed infrastructure. This task commits only an unnumbered **test resource**, not production role creation. Qualification creates login secrets from random UUIDs in memory; no password is stored or printed. Preexisting production roles/ACLs must be inspected and unsafe attributes, memberships, grant options, unexpected grants or ownership rejected rather than silently adopted. Trusted superuser/owner administration remains outside the runtime attacker boundary.

## Function and search-path amendment

The base historical DDL remains byte-aligned with its accepted blueprint. Its explicit ACL/ownership overlay is [historical_lineage_acl_candidate.sql](../../applications/marketplace-operations-persistence-postgres/src/test/resources/room-lineage/historical_lineage_acl_candidate.sql). Five functions remain SECURITY INVOKER. Only `publish_marketplace_sales_revision()` is SECURITY DEFINER: the owner inserts the exact receipt inside the already validated V018 transition, while the runtime has **no direct receipt INSERT**. No caller-controlled dynamic SQL or new entrypoint is introduced. Runtime cannot attach this function to another table because it lacks its EXECUTE privilege; direct trigger-function invocation is not a publication API.

All six functions set `search_path=pg_catalog,public,pg_temp`. Public CREATE is revoked from PUBLIC and not granted to runtime/owner. Public is the protected application schema; pg_temp comes last so temporary row types/tables cannot win resolution. PUBLIC EXECUTE is revoked from all six; only the boundary validator is executable by runtime. PostgreSQL trigger execution is not converted into a general direct EXECUTE grant.

The real writer and reader now set the same LOCAL search_path inside their owned transaction. This reusable runtime safety change prevents their unqualified SQL from selecting a session's shadow tables. A poisoned runtime connection with temporary subject/header/receipt objects and hostile initial search_path still publishes and reads the real public revision/receipt. Definer and invoker validation retain all immutability/exact-membership checks.

## Operation-level privilege matrix

| Object/operation | Exact privilege basis | Mutating / owner-only / runtime required |
|---|---|---|
| V015 subject identity lookup and FOR NO KEY UPDATE | SELECT organization_id, marketplace_order_id, currency, marketplace_key, external_order_id; UPDATE(currency) solely for row-lock eligibility | Lock only; not owner-only; required. V015 rejects currency changes and no-op writes without journal advance; runtime lacks current_version UPDATE |
| V015 journal boundary/trigger | SELECT organization_id, marketplace_order_id, evidence_version, change_sequence | Read / no / yes |
| V015 identifiers | SELECT organization_id, marketplace_order_id, observation_id, evidence_version, identifier_kind | Read / no / yes |
| V015 facts | SELECT organization_id, marketplace_order_id, fact_id, evidence_version, family, observed_at | Read / no / yes; no fact payload/source/money SELECT |
| V015 attempts | SELECT organization_id, marketplace_order_id, attempt_id, evidence_version, family, attempted_at | Read / no / yes |
| V015 corrections | SELECT organization_id, marketplace_order_id, correction_id, evidence_version, superseded_fact_id, replacement_fact_id, observed_at | Read / no / yes |
| Revision header | SELECT; INSERT on the writer's eighteen explicit columns, excluding generated projection_revision | Insert / no / yes; explicit identity override denied |
| Members, corrections, reasons, coverage | SELECT and INSERT on these four exact tables | Insert / no / yes; late inserts sealed; UPDATE/DELETE/TRUNCATE denied by ACL |
| V018 current projection | SELECT and INSERT; UPDATE only source_evidence_version, state_kind, assembly_policy_version, calculation_policy_version, calculation_kind, state_payload, last_applied_change_sequence, projected_at, current_revision_id | Update / no / yes; PK UPDATE excluded; immutable publication/context/dual guard remains mandatory |
| Publication receipt | SELECT to runtime; INSERT only through owner-context publication trigger | Insert / owner-mediated / no direct runtime INSERT |
| Generated identity sequence | No runtime USAGE/SELECT/UPDATE | Server identity allocation works with column INSERT; arbitrary nextval/setval denied |
| Boundary validator | Exact EXECUTE on public.validate_marketplace_sales_revision_boundary(uuid,uuid,bigint) | Read/validate / no / yes |
| Other five trigger functions | No PUBLIC/runtime direct EXECUTE | Invoked only via trusted installed triggers |
| Schema/DDL/owner controls | No runtime CREATE/TRIGGER/ownership/membership/grant option | Owner/deployment administration only |

The same six bounded source SELECT sets are required by the NOLOGIN owner because deferred receipt checks preserve the owner execution context of the definer INSERT. The initial restricted campaign exposed this exact missing privilege; granting these column sets fixed it. No source UPDATE is given to owner. This is not a general source-table read grant or a second runtime login.

Existing wider application authority is not inherited by the new role. The worker's SQL scopes organization/order in every lookup; its database role remains a trusted multi-tenant internal worker, not a tenant login or raw-evidence viewer. There is no new RLS claim, HTTP read permission or endpoint. An independent outsider identity cannot SELECT any history table or execute the validator. PUBLIC historical access is absent.

## PostgreSQL qualification and negative campaign

Fresh `postgres:18.4` Testcontainer, direct postgres migration identity, one inspected 127.0.0.1 PostgreSQL binding, Flyway baseline through V042 only, candidate and ACL overlay in one transaction, independent restricted runtime JDBC connections. V043, shared databases, existing containers and production identities are not used. The original eighteen lineage cases now run publications/reads and injected writer connections under the restricted role; administrative fixture source creation/catalog checks/intentional corruption remain explicitly postgres operations.

Catalog proof checks seven table owners, identity owner, six function owners/security/config/ACLs, all runtime attributes and memberships, PUBLIC ACLs, table/column privilege matrix and no sequence privileges. Source column grants are compared exactly for runtime and owner, not inferred from a table-owner test session.

Negative runtime SQL proves denial of DROP/ALTER history, DISABLE TRIGGER, TRUNCATE, DELETE/UPDATE history, receipt INSERT, protected-schema CREATE, function ALTER/REPLACE, SET ROLE owner, ALTER OWNER, SUPERUSER escalation, identity override/setval and trigger creation. Attempted self-GRANT cannot add UPDATE; PostgreSQL may warn rather than error, so the test checks the resulting effective ACL. Existing privileged immutability/corruption tests still prove the secondary trigger layer and restored enforcement. No trigger is weakened for ACL qualification.

The full restricted campaign retains R1/R2, unresolved→Ready/Incomplete, F1→F2→F3, exact/divergent duplicate, tenant/source/correction validation, manifest round-trip, eight failure injections, independent-backend races and lost COMMIT acknowledgement reconciliation.

Cutover proofs cover real pre-DDL legacy publications, new writer denial on old schema, legacy NULL preservation, no invented backfill, legacy code rejection for genuine post-schema writes, and new restricted linked publication/read/retry. Separate retirement proof shows NOLOGIN **does not kill an existing backend**: it fences new connections, while explicit drain/termination removes the owned old backend. This is disposable mechanism evidence, not proof of production fleet inventory or orchestration.

## Construction inventory and cutover boundary

Entire repository Kotlin construction search (excluding generated build output): one production legacy construction in API `Application.kt:270`; legacy test constructions in `PostgresMarketplaceSalesIntelligenceProjectionTest` and `PostgresMarketplaceSalesIntelligenceLineageTest`. The historical writer has no production construction; all instances are in the lineage qualification class. No alternate CLI, worker, scheduler or manual-script constructor was found. Class declarations are not construction sites. Existing API startup invokes default Flyway migration, so future matching composition must separate governed deployment from restricted runtime startup rather than run it as postgres.

Schema/binary matrix: OLD+OLD supports baseline behavior; NEW+OLD denies new legacy publication by linkage triggers and retired credentials; OLD+NEW history writer returns integrity failure; NEW+NEW succeeds under qualified restricted identity. SQL denial alone is **not a startup guard implementation**. Old installed binaries cannot be retroactively changed: credential retirement, fleet exclusion and DB enforcement prevent their writes. The matching new binary must verify an exact trusted ordered migration/checksum manifest and full required catalog/ACL before composing its writer, as defined in the updated promotion plan. Table existence or observed-history adoption is insufficient.

## Results and residual gates

MIGRATION_IDENTITY_CONTRACT_READY=YES. OBJECT_OWNERSHIP_CONTRACT_READY=YES. RUNTIME_ACL_CONTRACT_READY=YES. FUNCTION_SECURITY_READY=YES. ROLE_SEPARATED_POSTGRES_PROOF=YES. NEGATIVE_ACL_PROOF=YES. LEGACY_WRITER_INVENTORY_COMPLETE=YES for repository source. SCHEMA_BINARY_COMPATIBILITY_DEFINED=YES. CUTOVER_CONTRACT_READY=YES. CUTOVER_DISPOSABLE_PROOF=YES, bounded as above.

ROOM_SCHEMA_PROMOTION_TECHNICALLY_READY=YES for the reviewed base-plus-overlay identity/ACL candidate; canonical full-chain execution remains unavailable until V043/slot eligibility. WRITER_COMPOSITION_TECHNICALLY_READY=NO: the matching exact-history startup guard and producer/checkpoint publication integration are defined but not installed in normal composition. No final numbered migration/checksum manifest exists. Fleet deployment attestation remains a later actual cutover proof, not something disposable tests manufacture.

Findings: BLOCKER 1 = Package V043 closure/canonical promotion and absent exclusive Room migration slot. HIGH 1 = matching startup/producer/fleet composition implementation and production-form qualification remain gated. MEDIUM 0, LOW 0. Runtime ownership, PUBLIC access, search-path poisoning, receipt forgery, identity sequence manipulation and privilege escalation findings are fixed/proven in scope. Raw retrieval, Room operation and execution/recovery remain blocked.

Validation commands: focused lineage test campaign and relevant domain suite via `gradlew.bat`; candidate SQL blueprint parser/alignment check; ACL overlay PostgreSQL execution/catalog proof; `git diff --check` and staged intended-scope review. No API interface or normal composition changed, so unrelated API/full-repository builds are not needed. Final unique test counts and execution time are recorded in the closing qualification update below.

## Closing qualification results

```powershell
.\gradlew.bat :applications:marketplace-operations:test :applications:marketplace-operations-persistence-postgres:test --tests '*PostgresMarketplaceSalesIntelligenceLineageTest' --console=plain
.\gradlew.bat :applications:marketplace-operations-persistence-postgres:test --tests '*PostgresMarketplaceSalesIntelligenceLineageTest.ACL source column*' --console=plain
python scripts/room_lineage/verify_historical_blueprint.py --parser-path C:\Users\xmz_r\AppData\Local\Temp\room-lineage-sql-parser
```

Final full focused campaign: BUILD SUCCESSFUL in 34 seconds; lineage aggregate 24.19 seconds. Domain 529 pass (unchanged domain task up to date in final run); PostgreSQL 26 pass, including the retained eighteen lineage methods, six ACL methods and two explicit cutover methods. These are 555 distinct methods, not repeated-run totals; zero failures/errors/skips. The later focused method additionally checks that restricted runtime cannot execute the deployment ACL body; it does not add a new test to the count. The parser/alignment check remains PASS with 41 base statements/six functions/13 declared FKs, and only claims static work; actual role/ACL execution is provided by the tests above.

Initial restricted failures were preserved in local Gradle reports/logs, diagnosed as owner-context deferred source SELECT denial, and corrected with the exact bounded owner column grants. One cutover assertion initially treated an identical stale legacy no-op as a new write; it was corrected to use a genuine later trigger, which rejects without bypassing constraints. No broad grants or disabled triggers were introduced to make those cases pass. Temporary diagnostics were removed from runtime code before final qualification.
