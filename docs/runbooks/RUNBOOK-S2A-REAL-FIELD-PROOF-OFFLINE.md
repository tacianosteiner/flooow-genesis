# S2A Real Field Proof — Offline Launcher Runbook

## Status

`REAL_FIELD_PROOF=HOLD`

This runbook documents the launcher boundary. It does not authorize execution, create a signer, create a service login, or permit provider activity.

## Invocation

The only command is:

```text
command-authority-ceremony execute-field-proof
```

`FLOOOW_FIELD_PROOF_INPUT_PATH` points to the nonsecret, strictly parsed input bundle. No secret is accepted as an argument.

Three independent database configurations are mandatory:

```text
FLOOOW_VERIFIER_DATABASE_URL
FLOOOW_VERIFIER_DATABASE_USER
FLOOOW_VERIFIER_DATABASE_PASSWORD
FLOOOW_ISSUER_DATABASE_URL
FLOOOW_ISSUER_DATABASE_USER
FLOOOW_ISSUER_DATABASE_PASSWORD
FLOOOW_RUNTIME_DATABASE_URL
FLOOOW_RUNTIME_DATABASE_USER
FLOOOW_RUNTIME_DATABASE_PASSWORD
```

Database passwords are deployment secrets injected into the process environment. They must not be committed, printed, copied into command arguments, or retained in evidence. The signing private key and command credential are forbidden environment inputs.

## Human gates

Before execution, independently confirm:

1. the exact organization, ML/Omie pair, order, references, evidence fingerprint and manifest window;
2. signer subject, key fingerprint, signer authority and authorizing institution;
3. three distinct service logins and absence of cross-membership;
4. the displayed manifest, execution-plan fingerprint and durable IDs;
5. understanding that PRINCIPAL, INITIAL_CREDENTIAL and GRANT may commit independently.

The launcher proceeds only after the protected console receives the exact `EXECUTE <plan-fingerprint>` response.

## Interruption rules

- Never generate a new plan because an outcome is unknown.
- Replay uses the same principal, credential, grant, authority-operation and decision IDs.
- If INITIAL_CREDENTIAL exists after process restart, the original raw credential is unavailable. Stop with `CREDENTIAL_LOST_REQUIRES_HUMAN_REVIEW`.
- Never fabricate a replacement credential for the same credential ID.
- Never deliver a token twice.
- Never use ROTATE_CREDENTIAL or REVOKE as automatic compensation.
- A commit-unknown decision is inspected by its preserved decision ID.

## Post-proof reconciliation

Reconcile only organization/manifest/plan-scoped identities:

```text
s2a_accepted_attestation                 1 (or pre-existing exact replay)
s2a_attestation_consumption              1
command_principal                        1
command_credential_revision              1 at revision 1
command_permission_grant                 1 at revision 1, ENABLED
command_authority_operation              3, all linked to the manifest
marketplace_transaction_identity_decision 1
marketplace_transaction_identity_head    1
```

Global counts are not evidence. Missing, duplicate or mismatched lineage is `POST_PROOF_MISMATCH`.

## Prohibitions

```text
PROVIDER_CALL=NO
ROTATE_CREDENTIAL=HOLD
REVOKE=HOLD
SIGNING_PRIVATE_KEY_IN_LAUNCHER=NO
RAW_COMMAND_CREDENTIAL_PERSISTENCE=NO
DATABASE_OWNER_CREDENTIAL_IN_LAUNCHER=NO
```

## Read-only audit provisioning prerequisite

The runtime login must have SELECT on `public.flyway_schema_history`,
`s2a_accepted_attestation`, `s2a_attestation_consumption`, `s2a_signer_key_revision`,
`s2a_signer_authority_revision`, and `command_authority_operation`, in addition to
its existing SELECT on authority and decision tables. Frozen migrations do not
supply all these reads. An independently governed administrator must provision
these narrowly scoped reads to the runtime service login before any final gate.
The launcher never applies grants or repairs history. No migration is changed.

The audit also needs EXECUTE on these pure, SECURITY INVOKER functions and their
pure framing helpers (no authority-producing function is added):

```text
public.s2a_v042_authority_intent(text,uuid,uuid,uuid,uuid,uuid,uuid,bytea,uuid,text,text,uuid,uuid,text,text)
public.s2a_v042_authority_receipt(text,text,uuid,uuid,integer,uuid,integer,text,text)
public.s2a_v042_text(text)
public.s2a_v042_frame(bytea)
```

Existing runtime transaction-identity fingerprint functions remain in use.
Preflight checks read privileges, function security/volatility/EXECUTE privileges,
and every frozen V001-V042 history entry, SQL script identity, success flag and
Flyway CRC32 checksum. Missing history, failed migration, duplicate versions,
checksum mismatch or extra history fails closed, even when capability objects exist.

Reconciliation uses one PostgreSQL-enforced READ ONLY, REPEATABLE READ transaction
on the runtime connection, rolled back after inspection. It never calls the
accepted-attestation command verifier, issuer or writer. V041 canonical bytes,
JCA Ed25519 signature, accepted proof fingerprint and persisted signer/key lineage
are inspected directly. V042 consumption is bound to the manifest digest,
principal, correlation and principal-operation timestamps. All three exact plan
operations and receipts, authority rows, decision fingerprints and head must match.

An exact principal-only prefix can replay the same plan. Any credential or later
authority effect without a decision is terminal human review, including an
operation record whose target row is inconsistent. Decision/head prefixes always
enter read-only reconciliation; incomplete or mismatched state is refused.

Review tests use synthetic credentials and disposable containers only. They do
not authorize real execution or administrative provisioning.
