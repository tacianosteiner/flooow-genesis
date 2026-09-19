# SPEC-0086 — Controlled command authority provisioning

Status: VALIDATED CANDIDATE; real provisioning and field activation HOLD

Source decision: ADR-0086

## Scope

This contract closes the control-plane requirements for provisioning the V034
command authority substrate used by V035/V036. V037 and the injected-DataSource
PostgreSQL issuer implement it in isolated synthetic tests only. No runtime route,
configuration/secret change, provider call, canonical database write or token
generation is selected.

The only authority records are the existing V034 append-only tables:
`command_principal`, `command_credential_revision` and
`command_permission_grant`. V034/V035/V036 remain immutable.

## Preconditions

Before any operator session, all conditions must be independently true:

- an accepted authority source names the operator, organization, pair, exact
  permission, reason, provenance, correlation and approval expiry;
- organization is ACTIVE and both connection IDs exist in that organization with
  provider keys `br.com.mercadolivre` and `omie`;
- migration owner, offline issuer and runtime roles are distinct and their
  effective privileges have been tested in an isolated deployment-equivalent DB;
- the protected issuer tool passed synthetic tests for secret non-disclosure,
  parameter binding, rollback, lineage/retry and least privilege;
- V036 remains frozen and all V034/V035/V036 focused tests are green;
- no S2B policy or real field decision is bundled with provisioning.

Failure of any precondition denies the session. Absence of a record, grant,
provider observation or corpus is not interpreted as permission or zero risk.

## Transaction and lineage contract

Each operation uses one caller-owned READ COMMITTED transaction. Lock order is
organization SHARE, then exact principal UPDATE when it exists. The issuer
validates the current leaf and appends a legal V034 root or successor. It must
re-read the result before commit; an exception rolls back the full operation.

Principal creation requires a fresh principal UUID, immutable exact pair and
nonblank bounded reason/provenance/correlation. Credential revision 1 requires a
fresh credential UUID and `ENABLED` or `DISABLED` explicit state; a successor has
the same credential/principal, next revision and exact predecessor. Grant
revision 1 requires a fresh grant UUID, exact principal and one frozen permission;
a successor has the same principal/permission, next revision and exact grant
predecessor. The V034 triggers remain the final database enforcement.

Revocation is an append of a `DISABLED` current leaf. It serializes with identity
admission on the principal lock: decision committed first retains its immutable
historical lineage; revocation committed first denies a later decision. No tool
may alter or delete prior history.

## Secret contract

The tool generates exactly 32 random bytes with a CSPRNG, emits the canonical
`fc1.<credential UUID>.<base64url>` form only through an approved protected
delivery channel, and stores only V034's verifier. It receives no secret through
CLI arguments, env vars or interpolated SQL. It must use parameterized database
statements and redact exceptions. Its normal receipt excludes raw secret,
credential token and verifier. A `SecureString` prompt alone is insufficient
evidence of full process-memory secrecy; minimize lifetime and document that
runtime boundary.

## Executed adversarial proof

- no runtime role can append/revise authority, mutate history/head, DDL, TRUNCATE,
  disable triggers or change replication role;
- issuer cannot write identity ledger/head or policy tables; migration owner is
  not used by issuer/runtime;
- wrong organization, provider pair, stale/forked lineage, duplicate UUID,
  wrong permission and disabled parent all fail closed;
- raw secret, verifier and token are absent from arguments, environment, logs,
  receipts, error output, checkpoints and source-controlled fixtures;
- credential rotation disables the old admitted credential only when an explicit
  disabled successor is committed; grant revoke/admission races preserve V034
  ordering;
- rollback leaves zero partial authority rows; correlation-based retry is
  idempotent and never creates a second root;
- an enabled `DECISION_WRITE` grant cannot yield `POLICY_ADMIN`, S2B activation
  or a provider call.

V037 adds an immutable `command_authority_operation` ledger. Its org/operation
primary key is serialized with an advisory lock. Same operation ID and intent
returns the original nonsecret receipt; same ID with a changed intent fails
integrity. Initial credential binding additionally serializes the stable
principal and refuses a second credential identity for that principal. Rotation
uses the same credential identity and sequential V034 revision lineage.

Synthetic tests use PostgreSQL Testcontainers, apply V037 through Flyway, switch
to no-login issuer/runtime roles, and prove runtime direct INSERT denial and
issuer identity-head INSERT denial. They also prove principal issuance,
credential/grant issuance, `PostgresCommandAuthorization` interoperability,
rotation, revocation and concurrent root/initial-bind serialization. Receipts
contain IDs, revisions, state and fingerprints only; no test fixture logs or
stores a production secret.

Executed issuer-level proofs include concurrent rotation, grant-enable versus
revoke, cross-organization operation rejection and direct-SQL NULL/shape attacks.
Existing V034 regressions passed alongside them. Final adversarial diff review is
still required before any local commit.

## Field-proof gate

After an accepted implementation and deployment-role proof, a separate field
authority may authorize exactly one explicit S2A action. The action must use the
existing V036 writer, exact current V3/ML lineage, immutable decision/head,
tenant/cardinality safeguards and nonsecret receipt. It must not be automated,
infer authority from evidence or derive any economic conclusion. Until that
separate authority is accepted: real grants=0, decisions=0 and corpus=0.
