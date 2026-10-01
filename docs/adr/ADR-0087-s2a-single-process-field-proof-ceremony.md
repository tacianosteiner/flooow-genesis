# ADR-0087 - S2A single-process field-proof ceremony

## Status

Technical implementation proven. Real authority provisioning and real field execution remain HOLD pending unresolved approval-attestation/configuration contracts and explicit human approval.

The implemented technical foundation includes the single-process ceremony, mutable credential destruction, exact durable target binding, deployment-equivalent issuer/runtime separation, and V039 least-privilege runtime privileges. This status does not authorize a real field proof.


Date: 2026-09-23

## Context

V034 through V038 provide immutable command authorization, governed transaction identity, withdrawal semantics, role infrastructure, and durable source evidence. They intentionally create no real command principal, credential, permission grant, or identity decision.

A first field proof must demonstrate one explicit governed transaction-identity decision without turning an agent, provider evidence, a service bearer, or an operator tool into authority. `AGENT != AUTHORITY`. Durable evidence informs the writer; an explicitly approved command authority admits the immutable decision.

The initial design used separate credential-binding, authentication, and identity-confirm commands. That leaves no safe custody path for the raw credential between processes. This ADR closes that lifecycle gap.

## Decision

The first S2A field proof is one short-lived offline command named `execute-field-proof`. It is neither HTTP nor a provider connector, and it is not a migration seed, public provisioning route, runtime bootstrap, or direct-SQL fixture.

The command runs in one process:

```text
preflight
-> generate 32 random credential bytes in memory
-> issue one principal for the approved organization and exact ML/Omie pair
-> bind credential revision 1
-> one-time protected TTY delivery
-> grant TRANSACTION_IDENTITY_DECISION_WRITE
-> authenticate with the same in-memory credential
-> destroy raw credential material
-> execute the existing writer in one caller-owned transaction
-> post-proof verification
-> optional separately approved grant revocation
```

There is no raw-token custody between processes. The token must never enter a file, argument, environment, clipboard, shell history, transcript, log, receipt, database column, provider request, or HTTP request.

The command may only create the exact command-authority lineage required for one explicit transaction-identity action. It must not provision `TRANSACTION_IDENTITY_POLICY_ADMIN`, financial authority, Decision Room authority, provider-write authority, automatic identity authority, or a bearer fallback.

## Existing transaction boundary

The wrapper performs only read-only preflight. It must not add an external ML or Omie evidence fence.

`PostgresTransactionIdentityWriter` and the V035/V036 triggers own the authoritative transaction and preserve this order:

```text
organization FOR SHARE
-> principal FOR UPDATE
-> decision advisory lock
-> exact Omie V3 progress FOR UPDATE
-> sorted subject/target advisory locks
-> evidence/currentness validation
-> authorization recheck
-> immutable decision insert
-> derived head projection
```

Taking a progress lock before entering the writer would invert the established order and can conflict with ingestion. The existing writer and triggers are not changed for a ceremony wrapper.

## Role topology and V039 least-privilege contract

The migration owner, offline issuer, and runtime role remain separate. V037 grants the runtime no authority-row INSERT and grants the issuer no identity decision/head authority.

V039 removes PUBLIC EXECUTE from the V035/V036 transaction-identity functions and limits runtime execution to the helpers required by the initial CONFIRMED path. Withdrawal-specific execution remains excluded.

The final least-privilege model does not grant semantic UPDATE capability on integration_organization or integration_connector_progress. Two narrow SECURITY DEFINER row-lock helpers provide only the exact lock capabilities required by the established transaction order:

- command_authorization_organization_lock(uuid) acquires the exact organization FOR SHARE fence;
- transaction_identity_progress_lock(uuid,uuid) acquires the exact Omie V3 connector-progress FOR UPDATE fence, with the required capability fixed inside the helper.

transaction_identity_locks(...) remains SECURITY INVOKER and preserves the established V035 ordering. PUBLIC EXECUTE is revoked from the privileged helpers and the runtime receives only explicit EXECUTE.

The head remains derived through transaction_identity_advance() as SECURITY DEFINER; runtime receives no direct DML on it.
## Exact cardinality

With zero scoped rows before the ceremony and no immediate revocation, a successful applied proof produces exactly:

```text
principal | credential revision | permission grant | authority operation | identity decision | identity head
1         | 1                   | 1                | 3                   | 1                 | 1
TOTAL_EXPECTED_NEW_ROWS_AFTER_APPLIED_PROOF = 8
```

The three authority-operation rows are the issuer receipts for principal issuance, initial credential binding, and grant issuance. Authentication produces no row. The identity head is derived by trigger. Any other scoped delta is a kill condition.

A separately approved immediate revocation adds one disabled grant revision and one authority-operation row, making the cumulative delta 10. It is not the default behavior.

## Secret lifecycle

The future `CommandCredential` contract requires a mutable private byte array, idempotent `destroy()/close()`, byte overwrite, permanent invalidation after destruction, rejected digest/verifier use after destruction, no secret accessor, and a redacted `toString()`.

A JVM source `String` cannot be deterministically zeroized. A future generator must therefore originate in bytes and limit any textual token representation to the smallest TTY-delivery or immediate parsing scope.

## Human boundary

This ADR does not supply or infer accountable operator, approval source, approval window, revocation owner, credential custodian, credential delivery method, credential rotation owner, or immediate-revocation policy. Those are explicit human decisions. Evidence, a successful build, or a prepared command cannot substitute for them.

## Technical proof state

The disposable PostgreSQL 18.4 proof matrix has established:

- CommandAuthorization domain tests: PASS
- PostgresCommandAuthorization tests: PASS
- PostgresTransactionIdentityWriter tests: PASS
- FieldProofInput tests: PASS
- CommandAuthorityCeremonyPostgres tests: PASS
- V039 narrow lock model: PASS
- runtime semantic organization UPDATE: DENIED
- runtime semantic connector-progress UPDATE: DENIED
- PUBLIC privileged helper execution: DENIED
- exact target and integration-reference binding: PASS
- secret database/token surface checks: PASS
- git diff --check: PASS

These results establish the technical foundation only. They do not create human authority and do not authorize production execution.

## Remaining real-execution blockers

A signed, bounded approval manifest remains mandatory. The requirement is frozen, but its executable attestation contract remains unfrozen: signer identity, canonical serialization, signature algorithm, key custody, verification authority, duplicate/replay identity, and operational delivery have not been approved.

The real launcher configuration contract also remains unfrozen and the current launcher fails closed before constructing real issuer/runtime data sources.

The required human authority values remain absent and must not be inferred by software.

REAL_FIELD_PROOF = HOLD
REAL_AUTHORITY_PROVISIONING = HOLD
PROVIDER_CALL = NONE

## Consequences

The first proof remains deliberately narrow, accountable, replay-safe, and offline. It may prove one governed pair only after explicit approval and after the remaining real-execution gates pass. It does not activate S2B, financial authority, Decision Room authority, ExpectedSaleBasisPolicy, S3, C2, or provider activity.

## Rejected alternatives

- Multi-process token custody: cannot satisfy the no-file/no-env/no-argument/no-clipboard contract.
- Token transfer through environment, files, arguments, Docker environment, history, or logs: leaks durable secret material.
- External evidence fence: changes established lock ordering and can introduce deadlocks.
- Public provisioning route: expands the attack surface and violates issuer/runtime separation.
- Direct SQL fixture ceremony: bypasses the controlled issuer, typed authorization, and audited receipts.
