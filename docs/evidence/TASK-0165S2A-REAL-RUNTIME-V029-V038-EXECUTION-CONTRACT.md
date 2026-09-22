# TASK-0165S2A — Real Runtime V029–V038 Execution Contract

## Purpose and boundary

This contract authorizes no execution by itself. It freezes the conditions for a later explicit decision to authorize canonical runtime schema alignment from V029 to V038. Schema alignment is not authority activation. It creates no principal, credential, grant, identity decision, financial authority, ExpectedSaleBasisPolicy, Decision Room activation, S2B, S3, or C2.

## Repository identity

`PRE_CONTRACT_HEAD=f3d9efa81f2f9f295c30b905a8ef025178faa8c6`.

`EXECUTION_REPOSITORY_HEAD=TO_BE_FROZEN_AFTER_THIS_CONTRACT_COMMIT`. A commit cannot reliably contain its own final SHA: changing the file changes the commit. The execution decision must obtain the committed SHA, then require `HEAD` and `origin/main` to equal it. Documentation changes must not alter the migration package.

## Immutable package

Migration location: `applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration`.

| Migration | SHA-256 |
|---|---|
| V030 | d0c9479cb152f1793fd3b7d4d4a7b072a5b29f813feb7444a38241b4ab85a248 |
| V031 | f7131a21178d3ed17b154ff2b574d5f27b6d8b57c913f025f384a90424e53ba7 |
| V032 | 35f00160e777312f39080257ee755d91e067bff461e5aae6f44ae1aaf4a96289 |
| V033 | eb37c36c9be3025054592048ed910421b9df905ea00c9b31b860bfaccf52e3e4 |
| V034 | 8745476ccc76d6d0b9b100489f317f6cead44afd0072998401d94c3b595bc5d9 |
| V035 | 697cb21228ceb0237462c59fa70db9d92e673c7e8b034dfc68964ccd01703030 |
| V036 | 57fd0e49be6cd5a382009e8af22cfe603ab4c960fe5084ca79404916a4d175cc |
| V037 | c19a45d17774450747e1f4f6ad50745a085b37b621abbe1937f134bf688604ce |
| V038 | a9e6388595e63f5bd541ffcacf247847983b3fc48e23bc7e1695574f429b626b |

`MIGRATION_PACKAGE_SHA256=00544f9280bb510b7540d207dfe3562e92424ed69f22e9ae2a4ebd1b16cd3511`.

Aggregate algorithm: exactly V030–V038; ordinal, case-sensitive filename order; each UTF-8-without-BOM line is `filename:lowercase-sha256` followed by LF; SHA-256 covers all bytes including final LF. Any mismatch aborts.

## Platform and Flyway contract

PostgreSQL is exactly `18.4`; compose tag is `postgres:18.4`. Flyway core and PostgreSQL module are exactly `13.2.0`. The execution must use only the migration location above, `outOfOrder=false`, `validateOnMigrate=true`, and explicit `validate` before `migrate`. Repair, clean, baseline, manual history edits, SQL downgrade, unexpected cherry-pick, relaxed ignore patterns, and a target beyond V038 are prohibited.

## Numeric kill thresholds

Pre: successful Flyway count/version `29`; V021 `85`; V022 promotion `21`; V022 registry `12`; V026 Omie `400`; authority and identity tables absent.

Post: highest successful Flyway version `38`; failed rows `0`; V021 `85`; V022 promotion `21`; V022 registry `12`; V026 Omie `400`; principals, credentials, grants, authority operations, identity decisions, identity heads, V033 base evidence and V033 line evidence all `0`. `NUMERIC_TOLERANCE=0`: any difference aborts.

## Stages

A `REPO_AND_RUNTIME_PREFLIGHT`; B `MAINTENANCE_ENTER`; C `REAL_V029_SNAPSHOT`; D `REAL_V029_SNAPSHOT_VALIDATION`; E `POST_SNAPSHOT_V029_REVALIDATION`; F `FLYWAY_VALIDATE`; G `V029_TO_V038_MIGRATE`; H `POST_MIGRATION_DATABASE_ASSERTIONS`; I `POST_MIGRATION_TARGETED_REGRESSIONS`; J `MAINTENANCE_EXIT`.

A failure blocks all later stages. F must pass before G. G failure preserves failed database, snapshot and logs; no repair, automatic rollback, or writer restart. H or I failure keeps API stopped. J occurs only after H and I pass.

## Maintenance, snapshot, and session contract

Declared topology: postgres is POSTGRES; api is WRITE_CAPABLE; economic-decision-room-web, otel-collector and jaeger are read-only for PostgreSQL. Revalidate runtime topology locally; any unexpected writer aborts. Stop API, prove stopped, inspect sessions, stop PostgreSQL cleanly, snapshot, validate snapshot, restart PostgreSQL, revalidate V029 fingerprint, validate, migrate, assert, regress, then restart API.

The real snapshot is not created yet. It must be unique, timestamped, made before V030 from the canonical stopped V029 volume, copied with the source mounted read-only, and preserved. Required offline structure: `PG_VERSION` containing 18, `global/pg_control`, `base/`, and `pg_wal/`. Rehearsal evidence does not substitute for this asset.

```sql
SELECT pid, usename, application_name, client_addr, state, xact_start, query_start, wait_event_type, query
FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()
ORDER BY xact_start NULLS LAST, query_start;
```

```sql
SELECT a.pid,a.usename,a.application_name,a.state,a.xact_start,c.relname,l.mode,l.granted,a.query
FROM pg_locks l LEFT JOIN pg_class c ON c.oid=l.relation LEFT JOIN pg_stat_activity a ON a.pid=l.pid
WHERE c.relname IN ('marketplace_transaction_identity_decision','marketplace_transaction_identity_head')
ORDER BY a.xact_start NULLS LAST,c.relname,l.granted;
```

## V036, identifier, and rollback review

V036 is acceptable only in a controlled maintenance window. It has no business backfill, DELETE, TRUNCATE, or decision creation; risk is relation locking and constraint/trigger transition on the identity decision/head relations. Identifier truncation warnings are accepted: static review found no distinct 63-byte-prefix collision.

`ROLLBACK_PROCEDURE_PROVEN=YES`; `REAL_ROLLBACK_ASSET=NOT_YET_CREATED`. On failure: no Flyway repair, history edit, SQL downgrade, or improvised forward migration. Preserve logs, failed database, snapshot, migration hashes, and runtime metadata. Restore requires a separate recovery decision.

## Post-schema authority boundary and decision

After V038: principal, credential, grant, authority operation, identity decision, identity head and real pair remain zero. ExpectedSaleBasisPolicy is UNFROZEN; financial authority and Decision Room activation remain HOLD.

`ENGINEERING_READINESS=PASS`.

`REAL_EXECUTION_AUTHORIZATION=NOT_GRANTED_BY_THIS_ARTIFACT`.

`NEXT_GATE=REAL_RUNTIME_SCHEMA_ALIGNMENT_EXECUTION_DECISION`.