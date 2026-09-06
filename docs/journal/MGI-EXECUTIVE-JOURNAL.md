# MGI Executive Engineering Journal

Status: Active

Purpose: provide a durable executive record of MGI/Genesis convergence,
decisions, delivered changes, validation, risk, debt, and the next objective.

This journal records repository evidence. It is not a substitute for ADRs,
specifications, task evidence, commits, CI, or pull requests.

## Initial state - 2026-08-27

### Mission

Move Marketplace Growth Intelligence toward reliable real marketplace
decisions while preserving Flooow Genesis as the canonical Organizational
Computing platform.

### Starting repository state

- Genesis main: `dabbda8`;
- open PR: #132, TASK-0136 freshness contract;
- MGI code absent from Genesis and project `sources/`;
- user supplied the MGI v0.7.6 archive during the audit;
- no MGI branch or repository was found under the inspected GitHub accounts.

### MGI baseline received

- version: 0.7.6, Parallel Evidence Resolution;
- SHA-256:
  `B1B9D9A77189CC9E21901BCA991AF5BB4FAFDACD6381D9A8D3001CE6AF8EE0F6`;
- 194 isolated tests passed;
- real `.mgi` data and credentials were not inspected or changed.

### Genesis baseline verified

- PR #132 had successful CI, no conflict, and was merged normally;
- new main: `39993d3`;
- non-Postgres build baseline passed;
- 371 tests passed with zero failures/errors/skips;
- Postgres/Testcontainers tests were excluded locally, not bypassed in the
  already-green PR CI.

### Principal discoveries

1. MGI supplies valuable operational behavior and concrete provider learning.
2. Genesis already supplies the stronger canonical economic, financial,
   organization, connector, persistence, and audit foundations.
3. A wholesale port would create duplicate authorities.
4. The correct first convergence boundary is independent economic evidence,
   followed by durable ingestion and a fast projection.
5. MGI v0.7.6 has evidence-regression, orchestration-test, precision,
   transactionality, provenance-history, and tenant-isolation debt that must
   not be copied.

### Decisions

- accepted ADR-0041;
- established one convergence backlog in
  `docs/roadmap/MGI-GENESIS-CONVERGENCE.md`;
- retained MGI v0.7.6 only as behavioral baseline and controlled read-only
  transitional reference;
- preserved fast local reads as an invariant;
- preserved missing-is-not-zero and Ads-identity-is-not-allocation invariants;
- temporarily deferred, but did not cancel, TASK-0137 freshness implementation;
- prohibited live writes and autonomous action in the convergence foundation.

### Delivered in TASK-0138

- repository, branch, PR, task, architecture, and roadmap audit;
- archive integrity and content validation;
- v0.7.5-to-v0.7.6 semantic diff;
- isolated MGI test reproduction;
- Genesis build/test baseline;
- convergence ADR, roadmap, evidence report, and this journal;
- completion and merge of the already-green PR #132.

### Current risks

- no canonical live Mercado Livre or Omie adapter exists;
- no durable Sales Intelligence projection exists;
- local MGI remains a single-user prototype with local credentials and SQLite;
- Postgres/Testcontainers tests were not run in the local audit environment;
- canonical `main` was reported by GitHub as unprotected during the repository
  audit, although the engineering workflow still forbids direct pushes and CI
  bypass;
- old remote branches remain and need later non-destructive repository hygiene
  review.

### Debt accepted temporarily

- TASK-0137 freshness implementation is deferred;
- MGI v0.7.6 may remain a controlled read-only prototype until parity gates;
- operational UI work waits for canonical ingestion and projection.

### Next objective

Define the provider-neutral, organization-scoped independent economic evidence
contract and executable acceptance scenarios for:

- authoritative zero shipment cost;
- missing shipment cost;
- product COGS without ERP sales-order identity;
- invoice and tax evidence without ERP sales-order identity;
- Ads identity without Ads allocation;
- repeated missing refresh that does not erase accepted evidence;
- explicit correction and conflict behavior.

The task must remain pure: no live provider, persistence, UI, action, or Kernel
change.

## 2026-08-27 - TASK-0139 contract review

### Repository state before

- TASK-0138 merged through PR #133;
- canonical main: `d5cbc9c`;
- MGI v0.7.6 behavioral baseline and one convergence roadmap accepted;
- no production MGI feature started in Genesis.

### Decision

Accepted ADR-0042 and SPEC-0041 for one pure independent marketplace economic
evidence boundary. The contract reuses Genesis economics and makes accepted
facts, empty/failed collection attempts, conflicts, and explicit corrections
different domain events.

### Changes prepared

- exact evidence families and financial component mapping;
- external identity observations for payment, ERP order, invoice, and
  marketplace item-to-Ad-Group relationships;
- authoritative-zero and missing-attempt semantics;
- append-only evidence set and deterministic merge classification;
- explicit correction/supersession with retained history;
- provider-free MGI v0.7.6 acceptance scenarios;
- narrow TASK-0140 implementation authorization.

### Risk reduced

A later missing, ambiguous, or failed refresh is no longer allowed to overwrite
accepted financial or identity evidence. Ads identity is structurally unable to
become Ads allocation inside this boundary.

### Remaining risk

The contract is not durable until a later persistence task. No live provider,
projection, API, or operational screen exists yet. TASK-0137 inventory
freshness remains deferred.

### Next objective

Implement TASK-0140 exactly as specified, prove the MGI scenarios and
no-regression rules, then return to the durable ingestion dependency.

## 2026-08-28 - TASK-0140 independent evidence implementation

### Repository state before

- TASK-0139 merged through PR #134;
- canonical main: `8706c58`;
- ADR-0042 and SPEC-0041 authorized one pure implementation task;
- no production MGI feature or provider activation existed in Genesis.

### Decision

Implemented the independent marketplace economic evidence boundary as one
immutable, provider-neutral aggregate inside `marketplace-operations`. Accepted
facts, collection attempts, source conflicts, and explicit corrections remain
different domain concepts. Existing Economic Truth, ledger, and reconciliation
continue to own their respective meanings.

### Changes prepared

- organization/order/marketplace/currency subject isolation;
- exact financial and nonfinancial identity observations;
- authoritative-zero and missing-attempt separation;
- deterministic idempotency and source-fact conflict classification;
- explicit correction with preserved history and active replacement;
- canonical ordering, microsecond precision, and redacted rendering;
- 24 focused tests covering the 32 SPEC-0041 test-plan requirements;
- TASK-0140 evidence report.

### Tests and validation

- focused evidence suite: 24 passed;
- complete `marketplace-operations` suite: 231 passed;
- full non-Postgres build: passed;
- mechanical dependency, forbidden-reference, file-scope, and diff checks:
  passed locally;
- PR #135 CI: passed; merged as `e087548` on 2026-08-30.

### Risk reduced

Independently arriving shipping, product cost, invoice, tax, and Ads identity
evidence can now progress without an ERP order gate. Later missing or failed
attempts cannot erase accepted facts, and conflicting source facts cannot be
silently replaced.

### Remaining risk and roadmap impact

The evidence set is not durable across process restarts and is not yet
materialized into Economic Truth, ledger, reconciliation, or a fast read model.
P0.2 still requires its own accepted architecture and specification. No P0.2,
P0.3, provider, API, or UI work is authorized by this task.

### Next objective

After TASK-0140 passes PR review and CI, re-read canonical main and define the
smallest architecture/specification increment for durable append-only evidence
ingestion. Do not implement it as part of TASK-0140.

## 2026-08-31 - TASK-0141 strategic benchmark memory

### Repository state before

- TASK-0140 merged through PR #135 as `e087548`;
- the independent evidence boundary remained intentionally in memory only;
- core Trusted Commerce direction already existed in the Operating Model and
  Marketplace Trust roadmap;
- richer competitor, external-expert, and Commerce Network hypotheses remained
  outside GitHub in conversation and the local MGI strategic-horizon package.

### Decision

Preserve the unique strategic context as permanent innovation memory while
keeping GitHub `main`, the Constitution, accepted ADRs, and accepted
specifications sovereign. External success is useful evidence, not permission
to copy thresholds, workflows, vendors, technology stacks, or architecture.

### Changes prepared

- permanent Flooow Commerce Network strategic horizon;
- consultation and promotion rule for relevant future strategic decisions;
- distributed-commerce thesis and participant model;
- six candidate B2B, dropshipping, 3PL, allocation, and hybrid models;
- seller, supplier, logistics, payment, fiscal, return, dispute, authority, and
  network-effect hypotheses;
- explicit boundary between Flooow policy orchestration and regulated custody;
- TASK-0141 evidence and reconciliation record.

### Scope protection

No production code, module, dependency, API, schema, provider, score, payment,
fiscal rule, automation, Kernel change, or future implementation was
authorized. Existing Financial Trace, Reconciliation, inventory, connector,
and MGI boundaries remain canonical and must be extended rather than rebuilt.

### Tests and CI

- Markdown whitespace and `git diff --check`: passed;
- full local build excluding only Postgres/Testcontainers tests: passed;
- PR #136 complete CI, including persistent runtime validation: passed.

### Next objective

After PR validation and merge, inspect the latest `main` and derive the smallest
accepted ADR/specification increment for P0.2 durable append-only independent
economic evidence ingestion. Do not start P0.3, provider, API, or UI work.

## 2026-08-31 - TASK-0142 durable evidence contract

### Repository state before

- TASK-0141 merged through PR #136 as `a472f55`;
- TASK-0140 independent evidence remained deterministic but process-local;
- existing Postgres, organization, immutable Ledger, canonical observation,
  concurrency, and transactional-outbox patterns were reusable;
- no accepted durable evidence port, migration, adapter, or integration test
  existed.

### Decision

Accepted ADR-0043 and SPEC-0042 for append-oriented relational evidence history,
domain-merger replay, one optimistic subject version, duplicate-before-stale
retry semantics, and one atomic outbox notification for each newly applied
fact, attempt, or correction.

The contract follows the existing Financial Ledger lifecycle boundary:
historical reads and exact duplicate retry survive organization suspension,
while new mutations fail closed. A narrow persistence encoding bridge in the
application port avoids widening TASK-0140 domain constructors.

### Scope protection

TASK-0142 changes documentation only. It creates no database table, repository,
runtime wiring, projection, provider, API, UI, materializer, recommendation,
action, AI, or Kernel concept. Financial Ledger and Reconciliation remain
separate sovereign boundaries.

### Implementation authorization

TASK-0143 is limited to seven files enumerated by SPEC-0042 and 38 required
behaviors. If exact replay cannot be implemented without changing the accepted
TASK-0140 aggregate, implementation must stop for contract correction.

### Next objective

Implement and validate TASK-0143, then re-read canonical `main` before any P0.3
fast projection or live provider work.

## 2026-08-31 - TASK-0143 outbox contract correction

### Trigger

Implementation preparation after PR #137 inspected the actual V002/V005
outbox schema and delivery serializer. The accepted contract assumed a generic
outbox that did not yet exist.

### Finding

`assessment_id` was mandatory, database checks admitted only inventory-risk
events, delivery canonicalization retained only inventory-risk fields, and the
SPEC-0042 content type conflicted with the stored CloudEvents envelope contract.

### Decision

Stopped production implementation before commit. Accepted ADR-0044 and
SPEC-0043 to generalize the single outbox by explicit event type, preserve
inventory-risk byte compatibility, add the exact evidence CloudEvent family,
and reject arbitrary JSON or unknown event types.

### Scope protection

No schema, runtime, provider, API, UI, projection, materializer, Ledger,
Reconciliation, action, AI, or Kernel behavior changed in TASK-0143.

### Next objective

Implement TASK-0144 within the corrected nine-file scope and all combined
SPEC-0042/SPEC-0043 quality gates.

## 2026-09-01 - TASK-0144 durable independent economic evidence

### Objective

Persist independent marketplace economic evidence as an append-only,
organization-isolated journal with exact domain replay and a durable monotonic
cursor, without widening the production outbox boundary.

### Repository state before

- TASK-0140 supplied the immutable provider-neutral evidence aggregate;
- ADR-0045 and SPEC-0044 superseded the proposed outbox generalization with an
  organization-scoped `change_sequence` design;
- no accepted durable repository port, V015 schema, or PostgreSQL adapter yet
  existed on `main`.

### Decision

Delivered TASK-0144 in three reviewed slices: persistence contract, PostgreSQL
journal, and PostgreSQL adapter. The database owns `change_sequence`; the
adapter reconstructs state through the canonical domain merger and keeps
duplicate, conflict, lifecycle, and optimistic-version outcomes explicit.

### Changes delivered

- narrow persistence contract and redacted version encoding bridge;
- V015 append-only evidence schema and per-organization change sequencing;
- transactional PostgreSQL apply and repeatable-read reconstruction;
- correction history, organization isolation, rollback safety, and
  deterministic replay;
- bounded full-transaction retry for PostgreSQL `40P01` and `40001`;
- candidate-root collision handling through `ON CONFLICT DO NOTHING`, fixing
  the observed `23505` race without weakening subsequent locked validation;
- TASK-0144 evidence report.

### Tests and validation

- persistence contract and JVM surface checks: passed;
- V015 structural suite: 6/6 passed against PostgreSQL/Testcontainers;
- final adapter suite: 15/15 passed, 0 failed, 0 skipped against real
  PostgreSQL/Testcontainers;
- Flyway V001-V015 application and `git diff --check`: passed locally;
- PR and CI remain pending; no commit or push was performed at this checkpoint.

### Risks and debt discovered

Concurrent testing exposed and closed a deadlock/serialization retry gap and a
candidate-root unique-constraint collision. Durable evidence is still not a
fast projection, Economic Truth materialization, Financial Ledger entry, or
Reconciliation result, and no live provider supplies it yet.

### Roadmap impact

P0.2 now has a durable, resumable evidence journal suitable for a future
projection checkpoint query. TASK-0144 does not authorize P0.3, provider, API,
UI, outbox, Ledger, Reconciliation, automation, or Kernel work.

### Scope protection

Exactly the seven SPEC-0044 files changed. No eighth file, existing migration,
outbox runtime, dependency, provider, API, UI, projection, Ledger,
Reconciliation, or Kernel file was touched.

### Next objective

Complete commit, PR, CI, and merge review for TASK-0144. Only after canonical
`main` is updated should the next eligible roadmap increment be derived.

## Journal update template

Each completed convergence task appends:

```text
Date / task / PR / merge commit
Objective
Repository state before
Decision
Changes delivered
Tests and CI
Risks and debt discovered
Roadmap impact
Next objective
```

## 2026-09-03 - TASK-0145 durable evidence incremental change feed

### Objective

Deliver P0.3 Slice A as a separate, inward-facing durable economic-evidence
incremental change-feed boundary, with organization/projection checkpoints,
bounded Query B pending discovery, and compare-and-set advancement.

### Repository state before

- P0.2/TASK-0144 already supplied the durable V015 evidence journal and
  organization-scoped change sequence;
- ADR-0046 and SPEC-0045 accepted a separate four-operation Change Feed port;
- the P0.2 repository remained restricted to exactly find and apply;
- independent V015 test and SPEC acceptance hygiene commits were recorded
  separately from TASK ownership.

### Decision

Implement the separate MarketplaceEconomicEvidenceChangeFeed boundary and
V016 checkpoint table without widening the P0.2 repository, changing V015,
adding a journal index, or introducing scheduling/fairness state.

### Changes delivered

- four-operation application Change Feed contract and focused contract tests;
- V016 organization/projection checkpoint table with composite journal
  destination integrity and database-authoritative timestamp;
- PostgreSQL adapter for incremental changes, Query B discovery, checkpoint
  reads, and compare-and-set advancement;
- real PostgreSQL/Testcontainers integration, concurrency, migration,
  privacy, planner, and regression tests;
- detailed TASK-0145 execution evidence and 76-case traceability.

### Tests and validation

- Gate A focused application contract: 16/16 passed;
- Gate B focused PostgreSQL: 22/22 passed;
- Gate C marketplace-operations: 254/254 passed;
- Gate D persistence-postgres: 86/86 passed across 9 XML suites, including
  P0.2 15/15 and TASK-0145 22/22;
- Gate E full applicable build: BUILD SUCCESSFUL in 54s, 85 actionable tasks,
  29 executed and 56 up-to-date, with no test bypass;
- Gate F: 76/76 requirements passed; seven TASK-owned paths exactly;
- PostgreSQL 18.4, Testcontainers 2.0.5, and Flyway 13.2.0 applied V001-V016.

### Risks and debt discovered

Deterministic organization ordering with a bounded limit can starve later
organizations while earlier checkpoints do not advance. Fair scheduling,
leases, claims, workers, and Slice B materialization remain deliberately
unresolved and out of scope.

### Scope protection

TASK ownership is exactly seven paths: five implementation/test/migration
creations plus this TASK evidence and this journal entry. V015 remains
byte-unchanged, no new journal index exists, and no outbox, provider,
connector, API, UI, Ledger, Reconciliation, Kernel, scheduler, or build file
changed.

### Status

- status: ready for implementation commit human review;
- implementation commit: pending;
- push: not performed.

### Next objective

Obtain human review and explicit authorization for the TASK-0145
implementation commit. Do not begin P0.3 Slice B or another roadmap increment
before TASK-0145 commit, push, PR, CI, and merge governance is resolved.

## 2026-09-05 - TASK-0147 canonical economic truth assembly implementation

### Objective

Implement the smallest provider-neutral canonical Economic Truth Assembly slice that converts current independent economic evidence into either Ready(MarketplaceOrder) or NotReady without inventing order occurrence time, monetary values, coverage, applicability, provider meaning, or persistence semantics.

### Repository state before

- EXP-0008 had concluded Reject and established that current evidence could not canonically assemble MarketplaceOrder without explicit order occurrence evidence and stricter coverage semantics;
- ADR-0048 and SPEC-0047 were Accepted;
- SPEC-0046 was reconciled and Accepted as downstream projection contract only;
- TASK-0146 remained paused;
- no durable OrderOccurrence representation or migration existed.

### Decision

Introduce explicit OrderOccurrence evidence inside the existing independent evidence aggregate, assemble only from current activeFacts under marketplace-economic-truth-assembly/1, preserve MarketplaceEconomicTruthCalculator as the downstream truth authority, and keep PostgreSQL fail-closed until durable OrderOccurrence persistence is separately governed.

### Changes delivered

- explicit MarketplaceEconomicOrderOccurrenceObservation with microsecond precision, provenance, source-clock rules, fixed MARKETPLACE_ORDER family, redaction, duplicate/conflict identity, correction, history, and active-fact semantics;
- MarketplaceIndependentEconomicFact.OrderOccurrence integrated into the canonical evidence aggregate;
- MarketplaceEconomicTruthAssembler with Ready/NotReady and exactly the accepted three NotReady reasons;
- order occurredAt resolution from active OrderOccurrence facts only;
- Version 1 coverage mapping of active component presence to PARTIAL and absence to MISSING, with no automatic COMPLETE or NOT_APPLICABLE;
- exact EconomicComponent preservation and no monetary calculation inside assembly;
- PostgreSQL adapter compatibility guard that rejects unsupported durable OrderOccurrence observation and correction replacement through IntegrityFailure before durable mutation;
- real PostgreSQL/Testcontainers compatibility tests proving zero partial persistence and continued usability after rejection;
- TASK-0147 execution evidence.

### Tests and validation

- focused marketplace-operations suite: BUILD SUCCESSFUL;
- focused unsupported OrderOccurrence PostgreSQL/Testcontainers tests: BUILD SUCCESSFUL;
- complete marketplace-operations-persistence-postgres suite: BUILD SUCCESSFUL;
- complete repository gate: BUILD SUCCESSFUL in 4m 24s, 94 actionable tasks, 94 executed;
- git diff --check: clean;
- mechanical scope enumeration before documentation: exactly six implementation/test paths;
- no migration path changed;
- TASK-0146 remained absent from the working tree.

### Risks and debt discovered

Canonical assembly can now resolve order occurrence and construct MarketplaceOrder from current evidence, but real durable OrderOccurrence persistence remains intentionally absent. Until a separately governed persistence slice adds durable encoding and replay, production evidence loaded only through PostgreSQL cannot yet carry OrderOccurrence across restart.

### Scope protection

TASK-0147 owns exactly eight paths: four marketplace-operations implementation/test paths, two PostgreSQL compatibility implementation/test paths, the TASK evidence document, and this single executive-journal entry. No migration, provider adapter, projection implementation, API, UI, scheduler, build file, new component type, new evidence family, or TASK-0146 path changed.

### Status

- status: implementation complete; ready for implementation commit human review;
- local implementation and repository gates: green;
- implementation commit: pending;
- push: not performed;
- GitHub PR/CI: pending.

### Next objective

Obtain human review and explicit authorization for the TASK-0147 implementation commit. After commit, push, PR, CI, and merge governance are resolved, open a separately governed persistence slice for durable OrderOccurrence encoding before resuming TASK-0146 or Slice B implementation.

## 2026-09-06 - TASK-0148 durable OrderOccurrence implementation

### Objective

Close the final known persistence gap below canonical Economic Truth Assembly by
making `MarketplaceIndependentEconomicFact.OrderOccurrence` durable across
PostgreSQL restart without introducing a second evidence authority or changing
accepted evidence semantics.

### Implemented

- additive V017 migration for the dedicated OrderOccurrence subtype;
- parent durable fact discriminator widened to `ORDER_OCCURRENCE`;
- repository write and reload support for the exact canonical observation;
- existing transaction boundary reused for FACT and CORRECTION writes;
- correction replacement remains append-only with historical fact retention;
- restart-equivalent duplicate and source-fact conflict behavior;
- malformed durable subtype fails closed;
- existing durable evidence journal and change sequence remain authoritative;
- no provider mapping, backfill, new feed, new checkpoint, new repository
  abstraction, assembler change, calculator change, or TASK-0146 work.

### Local verification

- production Kotlin compilation: passed;
- test Kotlin compilation: passed;
- full `marketplace-operations-persistence-postgres` test gate: passed;
- focused
  `PostgresMarketplaceIndependentEconomicEvidenceRepositoryTest`: passed;
- V017/Testcontainers acceptance covers source-shape round trip, microsecond
  timestamps, restart, duplicate/conflict, correction, append-only protection,
  and fail-closed malformed history;
- `git diff --check`: no whitespace errors; only Windows LF-to-CRLF warnings.

### Governance state

Implementation is locally verified but TASK-0148 is not yet complete. The
remaining completion gates are final exactly-five-path verification, repository
CI, clean PR review, and merge. TASK-0146 remains paused until those gates are
closed.
## 2026-09-06 - TASK-0146 durable Sales Intelligence implementation

### Objective

Materialize current canonical marketplace economic truth into a durable,
organization-scoped, fast local Sales Intelligence projection.

### Implemented

- separate derivative projection port and processor;
- V018 durable current-state projection;
- monotonic guarded writes;
- canonical Ready/NotReady materialization;
- checkpoint-after-projection ordering;
- crash/replay safety;
- bounded keyset list/detail reads;
- organization isolation;
- representative-volume PostgreSQL index characterization.

### Local verification

Both marketplace application and PostgreSQL persistence module compile/test
gates passed, with exactly eight authorized paths and no upstream semantic,
provider, connector-runtime, API/UI, or historical migration changes.

### Governance state

Implementation is locally verified. Repository CI, clean PR review, and merge
remain required before TASK-0146 is complete.
## 2026-09-06 - TASK-0146 completion gate closed

PR #164 merged the durable Sales Intelligence projection into `main` at
`2917ec20a4e4d47baf6ea64b3f642748ef9057fd`.

Final verification:

- repository CI run #345 succeeded;
- final implementation head was `f5d41096a94e33af0a48e5eb24c69a2aeebc9b52`;
- the implementation remained limited to the eight authorized paths;
- V018 is the only migration introduced by TASK-0146;
- canonical evidence, assembler, calculator, provider, connector-runtime,
  API/UI, and research semantics were not expanded.

TASK-0146 is complete.

The next roadmap boundary is provider activation against the existing
provider-neutral Connector Runtime and canonical economic-evidence ingestion.
Connector Execution Coordination remains a later, separate contract.
## 2026-09-06 - TASK-0149 authorized: live Omie economic evidence ingestion

Accepted ADR-0050 and SPEC-0049.

The project moves from durable provider-neutral economic foundations to the first
live read-only provider evidence slice.

Decision:

- activate Omie PRODUCT_COST evidence first because static App Key/App Secret
  credentials already fit the existing Connector Runtime and Integration Control
  Plane without changing either contract;
- preserve `connector-runtime` as provider-neutral and infrastructure-free;
- create one vertical provider-ingestion module that translates provider records
  into the existing independent marketplace economic evidence contract;
- reuse historical MGI only for empirically validated provider mechanics and
  test knowledge, never as Genesis architecture authority;
- keep Mercado Livre live activation next, after a separate provider-neutral
  credential-rotation execution bridge exposes the Control Plane's existing
  versioned rotation safely to connector execution.

No production code is changed by this authorization PR.
Authorization refinement before implementation:

- durable Connector Runtime progress is explicitly kept in the PostgreSQL
  infrastructure boundary rather than simulated inside the provider module;
- SPEC-0049 now authorizes a reusable Postgres connector-progress store and the
  Omie economic-evidence page committer over existing connector progress/page
  tables;
- no migration or new table is authorized;
- provider module remains HTTP/record translation only;
- implementation scope is twelve paths.

## 2026-09-06 - TASK-0149 pre-implementation association correction

Executable contract review found that Omie product CMC is provider-level product
cost and does not itself carry a canonical marketplace order subject.

TASK-0149 was corrected before production code:

- Omie remains the first live read-only provider slice;
- Slice A durably records normalized product-cost source observations;
- V019 is authorized solely for those normalized provider observations;
- Connector Runtime and Control Plane remain unchanged;
- no fuzzy identity or order association is introduced;
- no order-level PRODUCT_COST evidence is created by TASK-0149;
- a later explicit association/promotion contract will bridge provider product
  cost to marketplace order economic evidence.

This preserves fail-closed economic truth while keeping provider activation
moving.
## 2026-09-06 - TASK-0149 Omie CMC endpoint correction

Official Omie documentation and historical MGI behavior were reconciled before
implementation.

Decision:

- CMC authority for Slice A is `estoque/consulta` / `ListarPosEstoque`;
- source field is `produtos[].nCMC`;
- pagination uses `nPagina` / `nRegPorPagina` / `nTotPaginas`;
- product/location observations remain provider-level evidence;
- zero CMC is retained as observed provider zero, not canonical zero product cost;
- currency remains unresolved in Slice A;
- historical MGI weighted-CMC normalization is not copied into the provider
  adapter;
- no write-capable Omie method is authorized.

This correction changes provider wire behavior only; Genesis truth, identity,
runtime, authority, and later association boundaries remain unchanged.
## 2026-09-06 - TASK-0149 implementation - live Omie product-cost source observation

Implemented the first production provider slice after canonical economic truth,
durable evidence, change feed, OrderOccurrence, and durable Sales Intelligence.

The slice is intentionally provider evidence, not economic truth:

```text
Omie ListarPosEstoque
-> exact product/location source observation
-> durable V019 provider observation
-> durable connector progress
```

Key boundaries preserved:

- static Omie credentials remain in Integration Control Plane custody;
- provider HTTP/auth/parsing remain outside Connector Runtime;
- `nCMC` is preserved exactly and is never silently converted to order COGS;
- currency remains unresolved;
- no fuzzy product/order identity is introduced;
- no MGI weighted-CMC logic is promoted into the adapter;
- no raw provider payload is retained;
- page durability precedes progress advancement;
- duplicate replay converges only when normalized rows agree;
- conflicting replay fails closed;
- no Economic Truth, Sales Intelligence, API/UI, OAuth, scheduler, or Kernel
  production code changed.

The next provider prerequisite after TASK-0149 remains the provider-neutral
credential-rotation execution bridge before live Mercado Livre OAuth ingestion.
## 2026-09-06 - TASK-0150 authorized: provider-neutral credential rotation execution bridge

TASK-0149 established the first real provider evidence path with static Omie
credentials.

Repository and provider research exposed the next correctness boundary:

- Control Plane already owns versioned credential replacement;
- Connector Runtime correctly excludes OAuth refresh;
- Mercado Livre refresh tokens are one-time and replaced after successful refresh;
- local post-refresh CAS cannot prevent two workers from attempting the same
  one-time remote credential.

Accepted ADR-0051 and SPEC-0050.

Decision:

```text
credential readiness
-> durable organization/connection/binding-version fence
-> one REMOTE_STARTED right
-> provider-specific refresh
-> existing Control Plane rotation
-> Connector Runtime only after credential readiness
```

V020 is authorized for coordination state only and stores no secret/reference.

CLAIMED may be reclaimed before remote start. Abandoned REMOTE_STARTED becomes
IN_DOUBT and is never blindly replayed for the same binding version.

TASK-0150 contains deterministic fake rotators only. Mercado Livre HTTP/OAuth
remains the next separately governed provider task.
## 2026-09-06 - TASK-0150 implementation - credential rotation execution fence

Implemented the provider-neutral credential-rotation execution layer required
before Mercado Livre live OAuth activation.

```text
Control Plane credential context
-> local readiness assessment
-> V020 binding-version fence
-> REMOTE_STARTED
-> one provider refresh result
-> existing versioned Control Plane replacement
-> COMPLETED / RETRYABLE / IN_DOUBT
```

Connector Runtime remains unchanged. No real provider rotator or OAuth request is
introduced. V020 contains coordination metadata only. CLAIMED work is reclaimable
before remote start; abandoned REMOTE_STARTED work becomes IN_DOUBT rather than
blind replay.

Next: separately govern Mercado Livre credential envelope + real refresh adapter,
then live read-only Mercado Livre economic evidence.
## 2026-09-06 - TASK-0151 authorization - Mercado Livre OAuth refresh

Authorized the provider-specific envelope and real one-attempt refresh adapter
required for Mercado Livre activation after TASK-0150.

```text
current Control Plane credential
  -> TASK-0150 binding-version fence
  -> Mercado Livre expiry assessment
  -> REMOTE_STARTED
  -> one POST /oauth/token
  -> validated replacement envelope
  -> existing Control Plane rotateCredential
```

Provider key is `br.com.mercadolivre`; refresh is single-use; provider
`expires_in` is authoritative; malformed/uncertain success and timeout/I/O/5xx
after request start are INDETERMINATE; invalid_grant is terminal
authentication-required. Connector Runtime remains unchanged.

Next: separately governed live read-only Mercado Livre economic evidence
ingestion.
## 2026-09-06 - TASK-0151 implementation - Mercado Livre OAuth refresh adapter

Implemented the provider-specific OAuth credential envelope and one-attempt
refresh adapter required for Mercado Livre live activation.

The resulting credential path is:

```text
SecretVault-held Mercado Livre envelope
  -> TASK-0150 credential-version fence
  -> local expiry assessment
  -> REMOTE_STARTED
  -> one POST /oauth/token refresh
  -> validated replacement envelope
  -> existing Control Plane rotateCredential
```

Safety properties:

- canonical provider key is `br.com.mercadolivre`;
- no hard-coded 3-hour or 6-hour token lifetime is used;
- replacement expiry derives from provider `expires_in`;
- a successful HTTP status with incomplete, malformed, or wrong-user replacement
  is `INDETERMINATE`;
- remote uncertainty after request start never authorizes blind reuse of the
  single-use refresh token;
- credential/token material remains SecretVault data and is redacted from public
  renderings;
- no OAuth callback, provider economic read, scheduler, provider write, or
  Connector Runtime production change is included.

Next: separately govern live read-only Mercado Livre economic evidence ingestion.
## 2026-09-06 - TASK-0152 authorization - live Mercado Livre order source ingestion

Authorized the first real read-only Mercado Livre economic-data acquisition after
the OAuth refresh bridge.

The slice is deliberately provider-level:

```text
Mercado Livre seller order search
  -> typed order/item/payment source records
  -> durable normalized source observations
  -> existing connector progress
```

It does not create a canonical economic subject because Connector Runtime does
not carry Genesis' internal `MarketplaceOrderId`.

Key decisions:

- reuse TASK-0151 credential codec through one scoped read helper;
- one remote GET per readPage;
- provider date filters are hour-granular, so progress uses only fully closed UTC
  hours;
- live source-hour completion stays non-terminal because Connector Runtime treats
  exhausted progress as final;
- source capability is `marketplace-economic.order-source`;
- offset/date-window exhaustion is retrieval state, not completeness;
- retain non-PII economic/identity source fields only;
- no raw JSON;
- no inline OAuth refresh;
- no direct independent economic evidence write;
- one additive V021 may normalize order/item/payment source observations;
- progress and source rows commit atomically.

Next after TASK-0152: separately govern internal marketplace-order identity
allocation/association and promotion into independent economic evidence.
## 2026-09-06 - TASK-0152 implementation - live Mercado Livre order source ingestion

Implemented the first production-capable, production-inactive Mercado Livre
seller-order source ingestion after TASK-0151.

The durable path is:

```text
current SecretVault OAuth envelope
  -> scoped seller/access-token read
  -> one bounded /orders/search GET
  -> closed UTC-hour source records
  -> normalized V021 order/item/payment observations
  -> existing atomic connector progress commit
```

Key safety properties:

- provider data remains source observation below Economic Truth;
- no Genesis `MarketplaceOrderId` is invented;
- no source amount becomes canonical revenue, fee, shipping, settlement, or tax;
- current-hour catch-up performs no HTTP and remains retryable/nonterminal;
- every successful page advances durable progress with `exhausted=false`;
- no buyer/seller PII, raw JSON, access token, refresh token, or client secret is
  persisted in source observation tables;
- provider 401 does not refresh inline;
- no Connector Runtime production change is included.

Next: separately govern marketplace-order identity allocation/association and
promotion from Mercado Livre source observations into independent economic
evidence.
## 2026-09-06 - TASK-0153 authorization - marketplace order identity and occurrence promotion

Authorized the first canonical promotion stage after live Mercado Livre order
source ingestion.

The governed path is:

```text
V021 durable order source observation
  -> exact (organization, marketplace, externalOrderId) identity registry
  -> one opaque internal MarketplaceOrderId
  -> immutable economic evidence subject
  -> marketplace OrderOccurrence from source date_created
  -> existing independent economic evidence repository
```

Key decisions:

- connection is provenance, not canonical business identity;
- internal UUID is random and never derived from provider order id;
- first source currency is immutable for the registry;
- equal re-observation is duplicate;
- changed source occurrence is explicit conflict, not silent correction;
- terminal source promotion outcomes are durably recorded;
- no TASK-0152 monetary source value is promoted in this task;
- no Connector Runtime/provider/OAuth changes are authorized.

Next after TASK-0153: separately govern financial-component promotion and then
explicit product/order-cost association.