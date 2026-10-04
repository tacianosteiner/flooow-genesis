# H02 governed production adapter scope

Baseline after validated phase A: `7f225b403d352f4b824a53c2df95d1372348ef8a`.
Authority: ADR-0090 and SPEC-0090 sections2/3/8/9/10/21.1/21.2/22.2.
H02_SCOPE_DEFINED=YES. H02_NEW_AUTHORITY_REQUIRED=NO.

The four bound logins, B/T/E proof, opaque request/result frames, durable
admission, trusted JCA sequencing, at-most-once delivery and independent
administrative reconciliation already have explicit contracts. Replacing the
legacy launcher composition is ordinary implementation of those contracts.
No role, identity, privilege, SQL function, relation, receipt subsystem, raw
projection or caller truth field is added. Normal-runtime V041/V042 adapters
remain for their existing authority; the governed executable never constructs
or calls them. Granting legacy rights to make that composition work is forbidden.

## Exact implementation

- Add a persistence protocol/codec containing the eighteen closed SQL statements,
  explicit JDBC casts and four slot mappings, primitive canonical frames and
  typed scope/execution/admission/delivery values. Static contracts are copied
  from SPEC, not from implementation generator maps.
- Add the pure immutable snapshot/JCA bridge beside the existing verifier. It
  receives only approved wrapper projections, verifies original manifest/key/
  signature/preimage/fingerprint, and issues no SQL. Audit verification uses
  the accepted tuple already approved for S03; it does not invent a signer subject
  or obtain a raw signer row.
- Add `GovernedOfflineFieldProofLauncher` and its four-source configuration.
  Replace the production `main` composition in `PostgresCeremonyComposition.kt`.
  The old normal-runtime writer/authorization/verifier/issuer implementations
  are absent from this governed call graph; their frozen dependencies remain.
- Use one source per VERIFIER/ISSUER/EXECUTOR/AUDITOR, with distinct configured
  login names, no membership inheritance and server-side bound session guards.
  Binding/incarnation/fingerprint/surface/history/ACL/policy expectations are
  the existing B/S01 client deployment configuration, not new authority fields.
- Bootstrap AUDITOR S01/S02/S03/S04 in read-only REPEATABLE READ/rollback, inspect
  every history row and preserve missing/null evidence. S03 EXACT requires
  independent JCA plus the exact caller command before reconciliation is reported.
- After eligible operator confirmation, generate protected execution proof and
  invoke EXECUTOR S13 once; any ambiguous commit stops for inspection, never
  blindly retries or rotates ownership. Preserve the returned server attempt,
  generation/execution/instance and original receipt/deadlines.
- VERIFIER S05/JCA/S06 uses one READ COMMITTED transaction. ISSUER pairs S07/8,
  S09/10 and S11/12 each use one independent transaction with immutable JCA.
  S10's returned fresh UUID alone supplies S14; a NULL replay UUID cannot deliver.
- Commit S14 before the one protected TTY attempt. Enforce its original server
  window conservatively using monotonic elapsed time; report S15 once. Failed or
  ambiguous delivery never retries/reissues; ADMIN handles residual uncertainty.
- Derive protected credential proof with the existing parser/verifier. EXECUTOR
  S16 returns a privately constructed admission handle bound to the current
  session/scope. Destroy token/credential/verifier buffers before the writer.
  No AuthenticatedCommand is fabricated from a caller UUID/boolean.
- EXECUTOR writer is a single method: S17, verify immutable snapshot/JCA, S18,
  commit on the same connection/read-write READ COMMITTED transaction. No API
  exports a transferable preparation or permits a second connection for APPLY.
- Errors roll back the owned connection and map to sanitized denial/replay/
  ambiguity classifications; neither error text nor object rendering exposes
  proof bytes. No automatic mutation retry or deadline renewal.
- Post-write AUDITOR inspection/JCA distinguishes exact effects from formal
  ceremony success. The local pending result maps to the already approved
  EFFECTS_COMPLETE/REQUIRED/NONE states; it grants no administrative recording
  capability and does not treat SQL EXACT as ceremony SUCCESS.

## Validation boundary

Independently compare actual production SQL/type vectors to SPEC/SQL AST; test
all eighteen calls with recorded prepared-statement binding/slot/transaction
ownership, real JCA vectors, wrong slot/scope, malformed/null transport,
rollback, fresh/replay delivery and one-connection S17/S18. Search the governed
production call graph for frozen function/raw authorization calls: require zero.
Tests use bounded mock JDBC or isolated extracted-body fixtures, not complete
V043, production identities/policy or protected volumes. M04 actual installed
ACL/frozen operational/concurrency proof remains deferred to separately
authorized G3F.4. The source interlock remains throughout implementation.

## Final source implementation disposition (2026-10-04)

Content independently compared with ADR-0090 and SPEC sections9,10,21.1,
21.2,22.2 and19. All proposed operational authority already exists.
H02_SCOPE_FILE_CONTENT_VALID=YES.
H02_SCOPE_FILE_MATCHES_AUTHORIZED_PHASE_B=YES.
H02_SCOPE_FILE_PROPOSES_NEW_AUTHORITY=NO.
H02_SCOPE_FILE_SAFE_TO_PRESERVE=YES.
Unknown untracked authorship is informational, not the content-safety oracle.

The final pure artifact/JCA bridge is `GovernedAttestation` in the ceremony
module; it uses the retained public domain codecs and verifier and issues no
SQL. `GovernedCredentialProof` is an isolated pure bridge in the authorization
module to the unchanged existing credential digest. It avoids an extra
immutable verifier object; the existing normal-runtime classes are unchanged.
The factory creates exactly four distinct pools from VERIFIER/ISSUER/EXECUTOR/
AUDITOR configuration. The previously composed RUNTIME pool is absent from the
governed executable. Binding/incarnation/canonical fingerprint, expected
history/ACL/policy digests and canonical policy bytes are independently approved
client deployment expectations for existing B/S01, not provisioned by this code.
The exact policy digest binds the local delivery margin to the server policy;
Q/S13 independently validate the actual approved policy and original preflight.

`GovernedCall` contains the exact18 SPEC21.1 input vectors. `GovernedFrame`
implements closed SPEC21.2 transports, presence, strict NFC UTF8, checked
microsecond arithmetic, type lengths and tag/order/trailing rejection. Frozen
issuer/verification tuples are transcribed from SPEC. No S18 private73-field
caller tuple is retained: S18 receives only the unchanged S17 preparation.
`GovernedSources` owns rollback/commit. `GovernedTransaction` enforces one
S17/JCA/S18 sequence and rejects direct S18 outside it, including on another
connection. `AdmissionHandle` is privately constructed only after validating
the current S16 response; no UUID/boolean AuthenticatedCommand is constructed.

`GovernedOfflineFieldProofLauncher` performs all authorized sequences. It does
not retry mutation or ambiguous commits. S10 fresh receipt alone supplies S14;
replay NULL cannot deliver. S14 commit acknowledgment and a conservative
monotonic original-window bound precede exactly one protected TTY invocation.
S15 reports once. All adapter-owned credential/proof/request buffers are
cleared before S17. Callback failure rolls back the same owned transaction.

Audit always executes S01/S02/S03/S04 in read-only REPEATABLE READ followed by
rollback. Complete history and its digest are checked; counts and observations
remain explicit. EXACT additionally requires original canonical manifest,
original signature/key, JCA, accepted-proof fingerprint, caller command,
JVM intent/decision fingerprints and retained evidence-binding fingerprint.
The local effect result remains pending independent administrative
reconciliation and never writes or invents canonical ceremony SUCCESS.
Exceptions are rendered only as DENIED_OR_AMBIGUOUS_REQUIRES_INSPECTION by the
executable; no SQL exception detail or proof/credential value is logged.

Recording JDBC tests exercise the real launcher and every18 statements with a
real TEST Ed25519 signature. They assert slot/argument order, separate commits,
read rollback, JCA tamper rollback, delivery replay/ambiguity/failure, proof
zeroization before writer, and unchanged one-connection decision handoff.
Independent SPEC/Kotlin negative review rejects name, argument, type, slot,
legacy dependency and connection-handoff mutations. These are source/adapter
proofs, not installed ACL, full frozen PostgreSQL or concurrency certification.
M04 remains RUNTIME_VALIDATION_REQUIRED; G3F.4 is not executed.
