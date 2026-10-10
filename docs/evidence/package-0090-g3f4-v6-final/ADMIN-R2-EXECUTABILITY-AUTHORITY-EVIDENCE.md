# ADMIN R2 executable and authority review — HOLD

Branch: `checkpoint/package-0090-cloud-handoff`. Inspection HEAD: `bd72e6463adbbf4d53c1500187a1cee99fea77c7`.
Origin/main: `77d482c97a663a527dcacc85036c7577dfc92782`. Evidence scope: G3F4 isolated rehearsal only.
Canonical baseline: NOT_READY / watchdog=false; all nine V6 registration rows absent.
Before/end allowlisted projection equal; policy SHA256 `e840fcadac2d5198a91cdb7b2345a31d4776cb3ead6e8b697391a4461a1a253d` unchanged.
Canonical mutation/T0/keypair/SIGN/ADMIN/TREG/runner: NONE. Test fixtures are separate.
Full root/migration projection, exact source chain, preserved hashes, and test results: [GATE-DATA.json](GATE-DATA.json).
ADMIN R2 SHA256: `c8ee2b6d06652d99db111a01956808f7488cde30f520e58d85114331a4a6d923`. Host-only authority is not full-runner execution authority.


R1 remains byte-for-byte preserved. Its frozen SHA is `13a8536c562831231f53e3de3b50932dc8187f7dbd39d3bd291500eef732a793`.
The actual dollar-quoted DO body has TWO psql references: incarnation_id and binding_id.
The focused prior audit count of one is contradicted by these bytes; the earlier two-count is correct.
psql does not interpolate inside quoted SQL bodies ([PostgreSQL 18 psql](https://www.postgresql.org/docs/18/app-psql.html#APP-PSQL-INTERPOLATION)).

Syntax concern audit: zero references inside R2 DO; literal UUID constants, ON_ERROR_STOP,
one BEGIN/COMMIT, constrained search_path, three exact-one rowcount checks, exact control poststate.
PG18.4 executes/resolves all ten embedded SQL statements in rolled-back, independent fixture transactions.
Ten negative full-script paths reject and leave fixture control state unchanged. Default false gate rejects first.
Individual statement resolution is NOT positive end-to-end activation proof.

Writer/authority concern audit: R1 self-authored watchdog timestamp/healthy=true; R2 removes both writes.
R2 writes readiness.state only and separately activates lifecycle/pointer. It consumes existing host health,
checks finite/nonfuture age <=100us before and after effects, and never rewrites the health timestamp.
No new role, grant, membership, function, policy, or authority route is added to the canonical deployment.
Disposable fixture role/table creation is limited to the test container.

These are two separate concern checks by the same operator, not independent reviewers.
No trusted host deployment/marker/history/catalog/continuous-watchdog proof was manufactured.
The named host grant permits artifact promotion only; it explicitly excludes ADMIN execution, T0, key, SIGN and runner.
R2 is therefore a gated candidate, not an authority-closed operational artifact, despite the required filename.
Its hard false must not be manually flipped in the canonical runtime.
Writer quiescence/fresh query-first after an ambiguous ADMIN COMMIT is not implemented
by this SQL transaction; it must be qualified by the complete future runner before promotion.

ADMIN_R2_SOURCE_CHAIN=PASS_PARENT_PIN_PRESERVED
ADMIN_SQL_PARSE_AND_NEGATIVE_EXECUTABILITY=PASS
ADMIN_WATCHDOG_SELF_AUTHORSHIP=REMOVED
ADMIN_ACTUAL_POSITIVE_ACTIVATION=UNQUALIFIED
WATCHDOG_WRITER_AUTHORITY=HOLD_INDEPENDENT_HOST_PROOF_ABSENT
ADMIN_ADVERSARIAL_GATE=HOLD

Native input manifest still pins R1. A governed successor must explicitly pin the corrected ADMIN hash;
this review does not mutate that frozen manifest or silently transfer its authority to R2.
