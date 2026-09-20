# ADR-0086 — Controlled command authority provisioning

Status: VALIDATED CANDIDATE; real field activation HOLD

Date: 2026-09-19

Baseline: `f3801f5965f71106467410f9cd7551f0d49c2b62`

## Decision

Use an offline, accountable operator ceremony for the first command principal,
credential and exact `TRANSACTION_IDENTITY_DECISION_WRITE` grant. It is a
separate control plane, never a public API, runtime bootstrap, migration seed or
service-bearer capability.

V037 implements the protected issuer seam and non-login database roles. It creates
no principal, credential, grant, token or transaction identity decision outside
disposable synthetic PostgreSQL. It does not authorize field activation by itself.

## Authority model

An accepted authority source must identify an accountable operator, exact active
organization, exact Mercado Livre/Omie connection pair, permission, reason,
provenance, correlation, rotation/revocation owner and bounded approval window.
Evidence about orders or providers cannot substitute for this approval.

The database issuer is distinct from the migration owner and application runtime.
The runtime may authenticate and authorize already-issued credentials, but has no
INSERT, UPDATE, DELETE, DDL, TRUNCATE, trigger-management or role-management
authority over `command_principal`, `command_credential_revision`,
`command_permission_grant` or the identity head. The issuer appends only the
audited authority rows permitted by V034; it cannot write identity decisions.

## Ceremony

The future protected tool executes one short-lived operator session over approved
TLS or protected local transport. It verifies the approved organization and pair,
reads current immutable lineage under the V034 principal lock, appends exactly
one requested revision, re-reads nonsecret lineage and commits or rolls back as
a unit. Lost responses are resolved by correlation and immutable lineage query,
never by blind retry.

Credential material is generated inside the protected tool using a CSPRNG. The
tool persists only V034's domain-separated SHA-256 verifier. Secret bytes must
not occur in command-line arguments, environment variables, PowerShell history,
transcripts, SQL literals, logs, checkpoints or receipts. Delivery uses an
operator-controlled protected channel. A receipt contains IDs, revision, state,
hashes of nonsecret request data and server time; it never contains a verifier or
credential.

## Allowed operations

1. Create an immutable principal bound to one active organization and exact
   Mercado Livre/Omie pair. It creates neither credential nor grant.
2. Append credential revision 1 or a sequential rotation/disable revision for
   that principal. Creating a new credential ID does not revoke another ID.
3. Append one exact enabled or disabled grant leaf for one frozen permission.
   `DECISION_WRITE` and `POLICY_ADMIN` remain independent; no wildcard/default
   admin, implication or policy activation exists.
4. Inspect nonsecret lineage and issue a nonsecret receipt.

## Consequences

Default deny remains until a legitimate enabled grant commits. A valid field
decision may only occur after the implementation and role-isolation gates in
SPEC-0086 pass, and only under separate accepted operational authority. One
field-proven pair would unlock research only; it does not establish economic
equivalence, ExpectedSaleBasisPolicy, S2B, S3 or C2.

`PostgresControlledCommandAuthorityIssuer` accepts an injected `DataSource`; it
does not introduce `DriverManager` in production code. It requires membership in
`flooow_command_issuer`, serializes operation/principal advisory resources and
records a nonsecret immutable operation receipt. V037 creates no-login
`flooow_command_runtime` and `flooow_command_issuer` roles; runtime has no INSERT
authority rows and issuer has no identity-ledger/head privileges.

The executed synthetic proof covers initial issuance, idempotent same-operation
replay, changed-intent failure, first-bind concurrency, stable-principal rotation,
grant/revocation concurrency, authorization interoperability, cross-tenant
operation rejection, direct role attacks, direct-SQL shape attacks and NULL-safe
ledger forms. The S2A2 candidate remains subject to final adversarial diff review.
Database owner/superuser and a compromised server remain outside this trust
boundary. Deployment-equivalent role/login configuration and human approval must
be accepted before any real authority row is created.
