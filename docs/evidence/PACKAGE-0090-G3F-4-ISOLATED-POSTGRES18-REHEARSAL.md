# Package 0090 — G3F.4 isolated PostgreSQL 18.4 rehearsal

**STATUS: HOLD — one HIGH finding required before G3F final.**

The approved `fixture-1` policy did not qualify the necessary watchdog freshness predicate on this isolated JDBC transport. All 40 measured ADMIN-to-AUDITOR heartbeat handoffs exceeded the actual 100 µs and approved maximum 200 µs: minimum 2190 µs, maximum 14426 µs. The experiment used warmed, distinct physical JDBC sessions and the actual PostgreSQL timestamp returned by the administrative update. It does not establish a full wrapper failure or universal impossibility; it establishes that this tested transport has no qualified positive readiness path under the approved fixture.

The fixture was not widened. Timing readiness remained NOT_READY with explicitly ineligible placeholder manifests. No operational binding was activated and no production policy was provisioned. The disposable container is stopped; its uniquely created volume is retained. G3G and G3F_FINAL_REAUTHORIZATION were not entered.

## Proven installed prerequisites

The frozen 42 migrations match the accepted Git baseline byte for byte in canonical LF content; working-tree CRLF hashes are recorded separately. Real Flyway applied V001–V042 and then the transactional temporary V043; history ends at 043 with zero failed rows. The temporary V043 is reversible to the canonical file by reinserting one exact first-fence byte span. Canonical V043 remains unchanged and fenced.

The approved native SHA-256 was reproduced and matched the installed library. PostgreSQL itself executed all 51 reviewed Ed25519 vectors with exact accepted/rejected parity. Installed catalogs confirm 18 wrappers, six executor signatures, exact owners and function metadata, and the 1040/32/8 V043 ACL sets with no missing or extra grants. Two Q function grants and one Q schema grant are separately governed prerequisites. Nine owner default-ACL probes showed no PUBLIC schema/table/function grants; temporary probe authority and objects were rolled back together. The explicit enum diagnostic showed owner-only USAGE. Generated row types reported PUBLIC USAGE, and an enum array reported no effective PUBLIC USAGE despite a NULL ACL. A targeted public-schema probe with all four actual service logins distinguished caller-supplied type construction from operational access: constructing (1) never revealed stored value 999; table SELECT/UPDATE and creation of dependencies on the explicit enum all denied with 42501. SPEC 24.2/24.3 preserves intrinsic associated row types and PostgreSQL creation behavior. The type-probe concern is closed with that limited normative interpretation; no operational default-ACL leak was demonstrated.

Four real dedicated PostgreSQL logins have no memberships, raw-table authority or private/frozen EXECUTE. The actual Kotlin adapter exercised 17 nonexistent-scope denial paths; S18 remained confined behind the failed S17 sequence. Direct installed JDBC calls covered all 18 signatures, every input NULL, malformed bytea and all wrong slots. The combined 274 calls produced only P0017 or 42501. They do not substitute for positive E2E, original-input A/B, foreign-binding or lifecycle coverage. Restart preserved policy, key commitments and successful migration history, but no durable effect/receipt replay was available to qualify the full recovery gate.

## Finding and exact technical handoff

**G3F4-H01 / HIGH / required before G3F final:** qualify a viable rehearsal-only temporal fixture before claiming positive runtime coverage. This is a fixture/transport qualification gap, not a demonstrated SQL authorization defect. No SQL authority changes are justified by these measurements.

Next action: prepare a versioned rehearsal-only fixture amendment for technical contract review; use measured transport bounds and a documented safety margin. Preserve the explicitly approved preflight TTL 1000000 µs / maximum 2000000 µs. A candidate to experiment with after that review is watchdog interval 10000 µs / maximum 20000 µs and health window 150000 µs / maximum 200000 µs, under a new fixture version, never as a mutation of fixture-1 or production policy. These proposed numbers are not authority or acceptance evidence. Then establish positive installed readiness under fresh heartbeats before resuming S01–S18, frozen semantic parity, A/B original-input verification, rollback, barriers/concurrency and durable restart replay. Only a completed G3F.4 PASS may lead to G3F_FINAL_REAUTHORIZATION.

Resolved probe concern M01 is retained in the installed ACL evidence, including the raw catalog expansion and actual service results. No ACL was changed to suppress intrinsic type behavior.

## Execution exceptions

An initial new internal-network bootstrap had no published JDBC port. It made no database connection; only its newly labelled container/network/volume were removed after identity checks. A default-ACL probe initially received 42501 because the owner correctly lacked database CREATE. The revised probe used one transaction containing temporary database CREATE, owner-created objects, catalog inspection and rollback. Neither exception was a migration failure, and no migration/history repair was performed.

A post-restart type-probe invocation failed with the previously assigned disposable port and produced no probe results. The current port was rediscovered from the uniquely labelled container before the successful repeat. Tooling now validates Docker project label, pinned image, exclusive new volume, read-only scratch mount and current localhost port before any Java JDBC connection. A Windows Go-template argument initially caused local endpoint validation rejection; JSON inspection replaced it. All 274 denial probes passed again with the final endpoint guard; a stale-port negative test was rejected locally before JDBC.

## Return fields

| Field | Result |
|---|---|
| DISPOSABLE_PROJECT | flooow-0090-g3f4-cc2941797db3 |
| DISPOSABLE_VOLUME | flooow-0090-g3f4-cc2941797db3-data |
| POSTGRES_VERSION | 18.4 (Debian 18.4-1.pgdg13+1) |
| POSTGRES_IMAGE_DIGEST | sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561 |
| V001_V042 | UNCHANGED_42_OF_42; FLYWAY_042_PASS |
| REHEARSAL_V043_DIFF | ONLY_AUTHORIZED_INTERLOCK_REMOVAL |
| V043_REHEARSAL_MIGRATION | PASS_TRANSACTIONAL; FINAL_VERSION=043; FAILED_ROWS=0 |
| NATIVE_RUNTIME_LOAD | PASS |
| NATIVE_RUNTIME_CRYPTO | PASS_51_INSTALLED_PG_VECTORS |
| INSTALLED_PUBLIC_WRAPPERS | 18/18 |
| INSTALLED_EXECUTOR_SIGNATURES | 6/6 |
| INSTALLED_COLUMN_ACLS | 1040; MISSING=0; EXTRA=0 |
| INSTALLED_FUNCTION_EXECUTE_ACLS | 32; MISSING=0; EXTRA=0; PLUS_2_Q_PREREQUISITES |
| INSTALLED_SCHEMA_USAGE_ACLS | 8; MISSING=0; EXTRA=0; PLUS_1_Q_PREREQUISITE |
| DEFAULT_ACL_LEAK | NO_OPERATIONAL_LEAK_IN_PROBES; INTRINSIC_TYPES_PRESERVED |
| REAL_ADAPTER_E2E | NOT_QUALIFIED; REAL_KOTLIN_DENIAL_PROBES_ONLY |
| DIRECT_LEGACY_SERVICE_CALL_COUNT | 0_IN_EXECUTED_ADAPTER_PROBES |
| FROZEN_OPERATIONAL_PARITY | NOT_EXECUTED |
| S10_S14_REAL_RUNTIME | NOT_EXECUTED |
| ORIGINAL_INPUT_RUNTIME_PARITY | NOT_EXECUTED |
| S13_COLD_RUNTIME | NOT_EXECUTED |
| ALL18_NEGATIVE_MATRIX | PARTIAL_274_CALLS; POSITIVES_FOREIGN_BINDING_LIFECYCLE_PENDING |
| REAL_ROLLBACK | NOT_EXECUTED |
| CONCURRENCY_SEMANTICS | NOT_EXECUTED |
| RESTART_RECOVERY | PARTIAL_POLICY_KEY_HISTORY_ONLY; GOVERNED_EFFECT_REPLAY_PENDING |
| BLOCKER_COUNT | 0 |
| HIGH_COUNT | 1 |
| MEDIUM_COUNT | 0 |
| LOW_COUNT | 0 |
| G3F_4_ISOLATED_POSTGRES18_REHEARSAL | HOLD |
| PROTECTED_DATABASE_CONNECTION | NO |
| PROTECTED_VOLUME_MOUNT | NO |
| PRODUCTION_SECRET_USE | NO |
| NEXT_GATE | G3F_4_REHEARSAL_FIXTURE_TIMING_QUALIFICATION |

Checkpoint branch: `checkpoint/package-0090-cloud-handoff`. The evidence commit and fetched remote equality are verified after committing these artifacts; the commit cannot contain its own SHA.

Evidence: [installed catalog](PACKAGE-0090-G3F-4-INSTALLED-CATALOG.json), [installed ACL](PACKAGE-0090-G3F-4-INSTALLED-ACL.json), [runtime tests](PACKAGE-0090-G3F-4-RUNTIME-TESTS.json), [concurrency status](PACKAGE-0090-G3F-4-CONCURRENCY.json).
