# SPEC-0083 — Dedicated command authorization

Status: Frozen for infrastructure only; operational activation HOLD

Date: 2026-09-18

Source decision: ADR-0083

## Closed implementation package and scope

Selectable slice: domain credential verification, stable authenticated actor,
V034 persistence and in-transaction grant resolution. No transaction identity
writer or HTTP route is part of this slice. No existing startup/configuration,
secret, provider credential, V033 data, frontend dependency or Kernel changes.
V001–V033 were inspected in the working tree; V034 is the next free migration.
V035 is not reserved for S3; future identity/policy numbering must be checked
again. The old build/audit V034 package remains a non-authoritative draft.

Implementation whitelist: this ADR/SPEC; Revision-9 additions in ADR/SPEC-0082
and TASK-0165S; CommandAuthorization.kt and its unit test in Marketplace
Operations; PostgresCommandAuthorization.kt and its integration test in the
PostgreSQL adapter; V034__create_command_authorization.sql. No runtime wiring.

## Credentials and actor

CommandPrincipalId is a server-stored UUID unrelated to secret material.
command_principal has composite PK (organization_id, principal_id), globally
unique principal_id and credential scope to exact Mercado Livre/Omie connection
IDs, same-organization composite FKs. A principal is immutable.

Token representation: fc1.<credential UUID>.<canonical base64url 32 random bytes>.
The UUID is a lookup selector, not an actor or tenant selector. Require exactly
43 canonical base64url secret characters and a canonical UUID. Generate using
SecureRandom in a future controlled provisioning ceremony; syntax alone does
not prove entropy. Persist only SHA-256 of a domain-separated secret in bytea,
with exactly 32 bytes. Use MessageDigest.isEqual on equal-length digests.
Neither candidate nor verifier appears in toString/errors. Invalid syntax,
unknown IDs, disabled credentials and inactive organizations authenticate as
absent. Unknown well-formed IDs also execute a dummy digest comparison. This
does not claim database lookup timing anonymity; ingress protection is an
activation requirement. No raw token is persisted, logged or checkpointed.

command_credential_revision PK is (organization_id, credential_id, revision),
with globally tenant-stable credential_id enforced by lineage. Each revision
references its principal; positive sequential revision with revision 1 having
no predecessor and later revisions exactly revision-1, same actor and ID.
State ENABLED/DISABLED. New verifier revision rotates the secret with immediate
old-token rejection and stable actor. A disabled row retains the previous
verifier; re-enablement/rotation is an explicit offline action. Revisions have
reason/provenance/correlation/decided_at from the controlled server/operator.
They are not grants. No expiry inferred from an absent value; this slice uses
explicit revocation, and activation must establish bounded rotation practice.

## Grants and audit

command_permission_grant PK (organization_id, grant_id); exact principal FK;
permission in the two frozen codes; ENABLED/DISABLED; revision > 0;
supersedes_grant_id; nonblank bounded reason/provenance; correlation_id;
decided_at server timestamptz. A unique index on org/principal/permission/revision
and one on org/supersedes_grant_id prevents duplicate roots and successor forks.
The predecessor trigger requires exact org/principal/permission, revision + 1
and current leaf. A latest DISABLED leaf denies; older ENABLED rows never
fallback. Independent decision permission cannot authorize policy admin.
All three tables reject UPDATE/DELETE. Credential and grant insert triggers
lock their stable principal row; hence revocation serializes with admission.
Database owners/superusers remain outside application trust and can bypass
triggers; restrict application DDL/TRUNCATE rights before deployment.
Indexes: credential lookup (credential_id, revision DESC), credential revision
PK; grant revision/successor uniqueness; principal PK and unique ID.

Exact trigger/function pairs: command_principal_immutable,
command_credential_immutable and command_grant_immutable use
command_authority_immutable; command_credential_lineage_insert uses
command_credential_lineage; command_grant_lineage_insert uses
command_grant_lineage; command_principal_scope_insert uses
command_principal_scope and checks exact provider keys br.com.mercadolivre/omie.
Provider lifecycle status is deliberately not an online-evidence prerequisite.

Before activation, use a migration owner distinct from the command runtime
role. Runtime requires SELECT on authority/scope rows and the narrowly granted
UPDATE column privilege on principal necessary for PostgreSQL FOR UPDATE; the
immutability trigger still rejects actual updates. Do not grant runtime INSERT
on principal/credential/grant, DDL, TRUNCATE or trigger-management rights.
Offline authority issuer alone may append audited revisions after its accepted
ceremony. Database role provisioning is an activation gate, not a seed in V034.

## Transaction boundary

authenticate(Connection, token) returns a server-derived authenticated command
containing organization, principal, pair, credential ID and revision. It conveys
no grant. It must never be constructed from request body or coarse bearer.

authorizeForWrite(Connection, actor, permission) requires autoCommit=false and
READ COMMITTED isolation. Caller owns commit/rollback; this adapter cannot open
or commit a second transaction. Lock organization FOR SHARE (ACTIVE required),
then principal FOR UPDATE, re-read exact current credential and exact current
permission leaf. Return Denied or Authorized(exact lineage). Organization
suspension, credential/grant revocation and rotation are rechecked here.
Infrastructure SQL errors propagate separately; malformed persisted authority
is a typed integrity failure, never ordinary denial or accidental permission.

Future S2A lock order: organization, principal, sorted organization-wide identity
advisory resources for subject and target; then re-read source/currentness,
cardinality, credential and grant immediately before immutable decision insert
in that same transaction. Existing principal lock remains held until commit.
Revocation trigger shares it: revocation committed first => DENY; admitted
decision committed first => its lineage remains historically valid. The second
authorization read uses the same connection and locks. READ COMMITTED ensures
fresh visibility after waiting; do not use an old repeatable-read snapshot.
Batch commands involving multiple actors are excluded; no inverse lock order.
Retry whole transaction on 40001/40P01 with bounded attempts and identical intent,
never partial writes. A denied transaction must not insert identity decisions.

Lineage: principal ID, grant ID/revision, permission, semantic version
command-authorization/1, SHA-256 canonical length-prefixed fingerprint of all
grant fields and authenticated scope. Historical decisions must persist this
lineage, plus credential ID/revision for admission audit. Later revocation must
not change its fingerprint. Credential rotation does not change grant lineage.

## Future API failure contract

Dedicated authentication only, no serviceBearer fallback. Missing/invalid
credential 401 AUTHENTICATION_REQUIRED; authenticated actor without required
permission 403 COMMAND_AUTHORIZATION_DENIED. Body parsing follows authentication.
S2A evidence gap 422 IDENTITY_EVIDENCE_UNAVAILABLE; conflict 409
IDENTITY_CONFLICT; integrity 500 IDENTITY_INTEGRITY_FAILURE; infrastructure 503
COMMAND_INFRASTRUCTURE_UNAVAILABLE. These extend existing problem conventions;
responses omit secret, verifier, foreign existence and grant internals. No
HTTP implementation or public provisioning API is authorized by this slice.

## Gates, attacks, tests and kill rules

Design review: credential theft/replay requires activation controls (residual,
no exposed route); spoofed principal/body/tenant cannot enter authentication;
wrong permission and zero grants deny; credential ID is globally bound to one
tenant; grant forks/foreign predecessors fail database constraints; revocation
and write admission share the same transaction lock; SQL failure never grants.
Relevant infrastructure slice: BLOCKER=0, unresolved authority-integrity HIGH=0.
This is an internal adversarial review, not an independent security attestation.

Required fresh tests: canonical parsing and altered/truncated credentials;
redaction; constant-time primitive usage; no seed authority; valid authentication
with no grant denied; independent permissions; credential rotation stable actor
and old-token denial; grant revocation/history; foreign tenant/FK/fork rejection;
immutability; revocation-first denies; admission-first blocks revoke until commit;
rollback releases locks; invalid transaction configuration rejected. Synthetic
fixtures exist only in disposable test PostgreSQL, never preserved S1 volumes.

Kill on any operational authority row/seed, bearer fallback, token output,
independent authorization/write transaction, source-volume mutation, automatic
policy code, unexpected whitelist diff or failing integrity/concurrency test.
Do not claim operational S2A proof from synthetic infrastructure tests.

Real field proof remains blocked until an accepted operator provisions an exact
decision grant. Then use the original candidate (58.28 equality is diagnostic,
not identity), exact current V3 and V021/V022 lineage, global cardinality,
immutable append/idempotent replay and tenant isolation. Record hashed lineage
and current exact grant. At least one governed field-proven CONFIRMED pair
permits ExpectedSaleBasisPolicy research only, not freeze or financial claims.
