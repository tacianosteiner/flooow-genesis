# SPEC-0084 — S2A explicit governed transaction identity writer

Status: Closed implementation contract; TECHNICALLY SELECTABLE

Date: 2026-09-18

Source decisions: ADR-0082 Revision 9, ADR-0083, ADR-0084

## Scope and migration

Base local commit f8d89a3d007f69616fc1f5145b8146ef19ef555e contains tested V034
command authorization. Inspecting the current migration directory confirms
V001–V034; select V035__create_explicit_transaction_identity.sql for this slice.
Historical S3/V035 reservation is SUPERSEDED. S2B/S3 future numbers unreserved.
V035 creates no principal, credential, grant, real identity row or policy.
No HTTP/startup/provisioning/provider/frontend/config changes. Domain/JDBC writer
is independently testable without activating a public route.

Closed whitelist: this SPEC and ADR-0084, TASK-0165S2A evidence,
TransactionIdentity.kt / TransactionIdentityTest.kt in Marketplace Operations,
PostgresTransactionIdentityWriter.kt / PostgresTransactionIdentityWriterTest.kt
in PostgreSQL persistence, V035__create_explicit_transaction_identity.sql.
No changes to V033/V034, existing auth implementation or S1 evidence.

## Intent, relation and failures

record(Connection, AuthenticatedCommand, TransactionIdentityCommand) requires
one caller-owned READ COMMITTED autoCommit=false transaction. Caller commits or
rolls back; SQL/infrastructure exceptions propagate separately. Typed outcomes:
APPLIED, ALREADY_APPLIED, AUTHORIZATION_DENIED, EVIDENCE_UNAVAILABLE,
CURRENTNESS_UNPROVEN, CONFLICT, INTEGRITY_FAILURE. Denied/invalid results must
not produce a decision; database integrity errors abort the transaction and
require rollback. No adapter opens/commits an independent authorization/write.

Intent fields only: decisionId UUID, sourceOrderReference, marketplaceOrderId,
kind CONFIRMED/REJECTED, reason EXPLICIT_CONFIRMATION/EXPLICIT_REJECTION/CORRECTION,
provenance, correlationId UUID, optional supersedesDecisionId. Bounded nonblank
references/provenance, no leading/trailing/control characters. Initial reason
matches kind; CORRECTION iff predecessor present. POLICY_EXACT_MATCH reserved
in the persisted vocabulary but explicitly CHECK-denied and not exposed in the
command enum. No tenant/connection/source coordinates/currency/fingerprint input.

Stable subject: org + Omie connection + sourceOrderReference. Relation adds
canonical marketplaceOrderId. Rejection affects that relation alone. Corrections
retain exact relation and require current leaf; rejected alternatives survive.
Historical stale confirmations keep reservations until an explicit correction.
The ledger and projection are shared future S2A/S2B decision universe, with
organization-global subject and target unique confirmed reservations.

No current API route. If a later route is selected: dedicated authentication,
401 invalid/missing credential; 403 valid principal/no decision grant; 422 evidence
or currentness gap; 409 conflict; 500 typed integrity; 503 infrastructure. No
serviceBearer fallback, public provisioning, cross-tenant existence disclosure.
HTTP tests are not applicable in this slice and no HTTP behavior is claimed.

## Durable evidence and deterministic selection

ML: server-selected principal ML connection; V022 registry key org/canonical ID,
marketplace mercado-livre; exact terminal PROMOTED/DUPLICATE promotion with matching
base V021 external_order_ref/currency and page/source FK lineage. Choose smallest
progress/ordinal among terminal equivalent lineages in that connection. Different
connections sharing one canonical target remain one identity and one reservation.
Record selected connection/capability/progress/ordinal plus canonical external ID
and currency. Foreign IDs or missing selected-connection promotion are unavailable.

Omie: exact org/selected Omie/sourceOrderReference V3 base rows, exact V033
sidecars and committed page (ordinal within record_count). Missing sidecar/page
or malformed fingerprint is integrity failure, not a substitute observation.
Validate all candidate rows: modified < created => integrity; both timestamps
missing anywhere => CURRENTNESS_UNPROVEN (unknown could be newest). providerRevision
= modifiedLocal ?: createdLocal; observedAt acquisition provenance only. Max
providerRevision candidates with different semantic fingerprints => CONFLICT;
equal semantic fingerprints => equivalent; then choose lowest progress/ordinal
for reproducible provenance. Never use arrival/ordinal to resolve semantic conflict.
Civil timestamps remain LocalDateTime, no timezone conversion/invention.

For explicit intent: current integration reference equal canonical external ID
corroborates; present unequal conflicts; missing neutral. Current nonnull Omie
currency unequal canonical currency conflicts; missing neutral. No monetary,
date, SKU/customer/origin match is authority. No older reference fallback.
Grant is independent explicit actor authority, exact durable joins are evidence;
neither can manufacture an automatic match or economic equivalence.

These current evidence mismatch guards apply to both decision kinds in this
slice. A contradictory newer revision cannot be bypassed to release an old
reservation; that command conflicts and requires a separately specified future
exceptional-governance contract. This deliberately preserves fail-closed authority
at the expense of liveness; rejected-A/confirmed-B remains supported when evidence
admission is valid (including neutral missing reference), never by old fallback.

## Exact schema and database enforcement

marketplace_transaction_identity_decision is immutable, PK(org,decision_id),
unique(org,Omie connection,source reference,target,revision) and unique(org,
supersedes_decision_id). Fields: relation, kind/reason/revision/predecessor,
selected V3 coordinates/semantic fingerprint/provider civil revision,
selected ML promotion coordinates/external ID/currency, principal/credential
ID+revision, grant ID+revision, exact permission, auth semantic version/fingerprint,
intent fingerprint, decision semantic fingerprint, provenance/correlation/server
decided_at. Composite same-org FKs to principal, credential revision, grant,
canonical registry, exact V022 promotion and exact V033 sidecar.

Every nullable CHECK explicitly requires predecessor NULL for root and NOT NULL
for correction; shape revision>0 and positive source ordinals. Root kind/reason
match; corrections require reason CORRECTION. Hex fingerprints/version/permission
are checked. BEFORE INSERT repeats authority/currentness/target/parent admission
under the shared locks and verifies fingerprints, so direct malformed insertion
fails. A SECURITY DEFINER AFTER INSERT function, pinned search_path and qualified
public tables, is the sole projection maintainer. Server decided_at is assigned
inside the insert trigger, not accepted from caller.

marketplace_transaction_identity_head PK(org,Omie connection,source reference,
target), exact decision FK, kind and decision ID. Partial unique indexes:
transaction_identity_confirmed_subject_idx(org,Omie connection,source reference)
WHERE kind='CONFIRMED'; transaction_identity_confirmed_target_idx(org,target)
WHERE kind='CONFIRMED'. Direct INSERT/UPDATE/DELETE rejected; only nested ledger
insert maintenance can insert/advance a head, and transition must refer to exact
current predecessor/relation. Deletion always rejected. Ledger UPDATE/DELETE
rejected. Schema owner bypass remains outside trust; runtime cannot DDL/TRUNCATE,
disable triggers, create triggers or directly write projection.

Functions: transaction_identity_hash (length-prefixed UTF8 SHA256),
transaction_identity_grant_fingerprint (matches command-authorization/1),
transaction_identity_locks; transaction_identity_validate (BEFORE ledger),
transaction_identity_advance (AFTER ledger), transaction_identity_head_guard,
transaction_identity_immutable. Trigger names use those same suffixes. No seeded
rows. No policy table. Check guards use IS DISTINCT FROM or explicit null tests.

Additional exact fingerprint helpers: transaction_identity_intent and
transaction_identity_fingerprint over the decision composite. All new functions
pin search_path=pg_catalog,public,pg_temp to prevent caller temporary-table
shadowing. Page storage must contain its declared count of base/sidecar rows
and its input version must precede locked progress; incomplete pages fail integrity.

## Lock order, currentness and revocation

One transaction: org FOR SHARE; principal FOR UPDATE through SPEC-0083;
decision-ID advisory lock; exact V3 progress row FOR UPDATE; sorted subject and
target advisory resources; resolve currentness/ML/history/cardinality; immediately
re-run authorizeForWrite exact TRANSACTION_IDENTITY_DECISION_WRITE before insert.
Ledger trigger repeats the same order. Shared locks held until commit/rollback.

Key material (hashtextextended(key,0), pg_advisory_xact_lock):
transaction-identity/id/1:<org>:<decisionUUID>;
transaction-identity/subject/1:<org>:<Omie connection>:<UTF8 length>:<source ref>;
transaction-identity/target/1:<org>:<canonical target UUID>.
Subject/target sort lexically; hash collisions cause extra serialization only.
Ingestion uses org/connection/provider-binding SHARE then same progress UPDATE;
identity never takes live provider binding/connection update locks, so no inverse
progress→provider lock. Auth revocation takes principal only, without progress/
identity resources. Different principals/connections share target advisory lock
and unique index. Single-command/single-source-connection transactions only;
batches and later automatic policy lifecycle must not introduce inverse order.

Revoke committed first => authorization denied. Admission locks held first =>
revoke waits; decision committed under exact grant remains historical authority.
Source ingestion committed first => new current V3 used; writer progress fence
first => ingestion waits until decision transaction ends. No pre-read snapshot.
No projection advance without ledger insert; rollback leaves neither.
40001/40P01 propagate for whole-transaction bounded retry by caller; ID replay
handles uncertain commit without authorizing a new decision or rewriting history.

## Fingerprints and replay

Canonical hash = SHA256 over ordered UTF8 byte-length-prefixed field strings,
version transaction-identity/1. Intent hash includes org/principal/server pair,
stable subject, target, kind/reason/provenance/predecessor. Decision semantic
hash adds selected ML lineage/canonical external ID/currency, V3 semantic
fingerprint/provider civil revision, and exact grant semantic lineage.
SQL checks the same ordered definition as domain code. Civil revision formats
yyyy-MM-dd'T'HH:mm:ss.SSSSSS. Equivalent V3 observation coordinates are provenance,
excluded from semantic hash after semantic equivalence; ML lineage is intentionally
included because it chooses authority-relevant source context. Predecessor and
grant IDs are intentionally semantic lineage. Decision ID, correlation, server
time and credential revision are admission/audit metadata, excluded from content
hash; credential rotation does not change business actor. First replay retains
original correlation/time/lineage even if a retry supplies a new correlation.

After current permission check and decision-ID serialization, same org/ID/intent
returns stored ALREADY_APPLIED without reinterpreting new source evidence or
replacing historical authority. Changed intent => INTEGRITY_FAILURE. Different
actor/pair cannot replay another actor's ID as their own. Grant revoked now denies
retry/read-through; revocation does not mutate stored history.

## Closed tests, review and kill rules

Fresh focused domain and PostgreSQL tasks must execute after final source/schema,
not only cached XML. Tests: intent validation/fingerprint determinism/nonsemantic
metadata; zero migration seeds; no/wrong/revoked/cross-tenant grant; historical
provider state; exact ML selected-lineage/multiple connections; stable subject;
missing-neutral/reference mismatch/currency conflict; unknown/bad civil timestamps;
equal semantic ties vs contradictory max/newer-current veto; exact replay/ID
collision; rejected A then confirmed B; corrections/non-leaf/forks; immutable
history/controlled projection; same subject/different target and different Omie
connections/same target races; progress-fence ingestion race; grant revocation
races; rollback and direct NULL/FK/enum/fingerprint/authority/projection attacks.
POLICY_EXACT_MATCH direct insertion fails; no future auto proof claimed.

Internal design attack review chooses canonical ID/server-bound lineage and
relation-specific rejection; projection adds DB uniqueness, no parallel universe;
currentness fence interoperates with real ingestion; read-committed/one connection
prevents auth/source TOCTOU; explicit NULL guards prevent the V034 defect class.
Relevant writer design BLOCKER=0 and unresolved authority-corrupting HIGH=0.
Final implementation tests/diff review are still mandatory before claiming proof.

Kill on provider call/write, operational seed/provisioning, real decision, policy
code, bearer fallback, ignored artifact staging, changed frozen migration/source
proof, unauthorized projection mutation, source/auth TOCTOU or failing tests.
Real authority field proof HOLD; governed real pair corpus=0. Keep original
candidate for future accepted provisioning proof; 58.28 equality remains only
diagnostic. Economic basis research needs >=1 real governed field pair, no freeze.
