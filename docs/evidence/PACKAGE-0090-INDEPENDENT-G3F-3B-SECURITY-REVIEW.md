# Package 0090 independent G3F.3B implementation/security review

Review date: 2026-10-04. Branch: `checkpoint/package-0090-cloud-handoff`.
Baseline: `9ba136cd4920d2710d6a886f0eea7cee938c3b2a`.
Initial fetch proved HEAD and origin at that baseline and a clean worktree.

**Decision: HOLD. BLOCKER=0; HIGH=3; MEDIUM=4; LOW=1.**
Do not remove the V043 interlock or enter G3F.4 on this review.
The prior composition checkpoint remains historical evidence; its claim of
18 implemented contracts is not an independent contract-conformance result.

This review changes evidence and a review-only extractor, not migration,
generators, native implementation, adapters, policy or production identities.
No V043 execution, protected database connection, G3G, main merge/push or
production secret use occurred. Focused tests used new disposable network-free
containers and extracted function bodies, never the complete migration.

## Method and independently reconstructed evidence

`scripts/validation/package_0090_independent_review.py` imports pglast, not
implementation generators, existing gate validators or their wrapper maps.
It parses actual SQL definitions/grants and the normative Markdown separately.
Its JSON records exact arguments, modes, return columns, security, volatility,
search path, owners, revokes, dependencies, writes and lock markers by function.
It compares every column grant against SPEC22.4 and exact function grants against
independently transcribed normative owner/dependency rows and frozen signatures.
Counts alone are not a PASS condition. The extractor is review evidence, not an
installed catalog checker or a complete PL/pgSQL correctness proof.

Evidence:

- `PACKAGE-0090-INDEPENDENT-SOURCE-REVIEW.json`: definitions, ACL differences,
  frozen tuples and 15 actual frozen call sites.
- `PACKAGE-0090-INDEPENDENT-NATIVE-REVIEW.json`: new pinned clean builds,
  vectors, operational injections, exports/imports/dependencies/hardening.
- `PACKAGE-0090-INDEPENDENT-ORIGINAL-INPUT-REVIEW.json`: new A/B executions on
  both audit and mutation paths; underlying focused harness limitations retained.
- `PACKAGE-0090-INDEPENDENT-MUTATION-REVIEW.json`: new actual I/E body execution,
  unchanged pure identity helpers, mock operational dependencies, independent
  S10 output decoding and the demonstrated contract mismatch.
- `PACKAGE-0090-INDEPENDENT-TEST-INVENTORY.json`: 189 actual test methods;
  count is explicitly not coverage or independence proof.

Existing isolated harnesses were inspected before reuse. They are supporting
executions, not independent normative oracles. The independent manifest and S10
decode contradict their PASS labels. Previously committed dynamic golden files
were restored byte-for-byte after focused runs; new results have separate names.

## A. Public surface

PUBLIC_WRAPPER_SIGNATURE_COUNT=18; PUBLIC_WRAPPER_CONTRACT_COUNT=18 normative;
EXECUTOR_SIGNATURE_COUNT=6. Only 16/18 normative name/type signatures exist.
Two other public names occupy S11/S12's positions. Nine of eighteen contracts
match both exact function name/type vector and exact input argument names.

| Stage | Actual entrypoint | Exact manifest assessment | Owner / slot |
| --- | --- | --- | --- |
| S01 | offline_preflight | Name/arguments/return metadata match | A / AUDITOR |
| S02 | offline_inspect | Name/arguments/return metadata match | A / AUDITOR |
| S03 | offline_reconcile | Name/arguments/return metadata match | A / AUDITOR |
| S04 | offline_read_history | Six TABLE columns, ordered rank, set result match | A / AUDITOR |
| S05 | offline_begin_verification | Name/arguments/return metadata match | V / VERIFIER |
| S06 | offline_persist_verification | `envelope` replaces `verified_envelope` | V / VERIFIER |
| S07 | offline_begin_principal | `envelope` replaces `principal_request` | I / ISSUER |
| S08 | offline_apply_principal | `envelope` replaces `verified_principal_request` | I / ISSUER |
| S09 | offline_begin_initial_credential | `envelope` replaces `credential_request` | I / ISSUER |
| S10 | offline_apply_initial_credential | Wrong argument name and public output envelope | I / ISSUER |
| S11 | offline_begin_permission_grant | Required `offline_begin_grant` missing | I / ISSUER |
| S12 | offline_apply_permission_grant | Required `offline_apply_grant` missing | I / ISSUER |
| S13 | offline_claim_attempt, nine inputs | Exact declared metadata match | E / EXECUTOR |
| S14 | offline_claim_attempt, twelve inputs | Exact declared metadata match | E / EXECUTOR |
| S15 | offline_claim_attempt, thirteen inputs | Exact declared metadata match | E / EXECUTOR |
| S16 | offline_authenticate_command | `credential_proof` replaces `derived_credential_proof` | E / EXECUTOR |
| S17 | offline_prepare_attested_decision | Exact declared metadata match | E / EXECUTOR |
| S18 | offline_apply_attested_decision | `decision_request` replaces `verified_decision_request` | E / EXECUTOR |

For all 18 actual definitions: no defaults/variadic inputs; CALLED ON NULL INPUT;
SECURITY DEFINER; fixed `pg_catalog,pg_temp`; S01-S04 STABLE, others VOLATILE;
appropriate owner; explicit PUBLIC revoke. Scalar results are bytea, S04 is
TABLE(record) with the six required columns and SETOF metadata. The only
same-name overloads are the three specified claim type vectors. All bodies
check the bound session OID/name and intended slot before scope/domain access.
Service EXECUTE allocation is a separate binding/provisioning prerequisite;
V043 grants none directly to service logins. Actual installed login ACLs have
not been proved. Wrong S11/S12 names are alternate entrypoints, not acceptable
aliases, and must be replaced rather than retained alongside corrected names.

## B. SECURITY DEFINER

All 24 actual function definitions are SECURITY DEFINER with a fixed
`pg_catalog,pg_temp` path. Application relations, row types and callable
dependencies in their bodies are schema-qualified. Unqualified CTE names,
record fields and SQL special forms such as COALESCE/LEAST/EXTRACT are not
application object resolution. No caller-selected dynamic SQL, identifier
interpolation, SET ROLE, regproc/regclass lookup, pg_temp relation reference,
search-path mutation, internal COMMIT or recursion widening authority was found.
Transaction isolation/read-only settings are checked as transaction requirements;
identity/authority comes from live session catalogs and immutable bound records,
not a caller GUC. Q additionally inspects live settings/catalog configuration.
The native bridge is a pure immutable scalar path with its approved strictness;
it projects no keys or originals. Trigger/helper ADMIN ownership is separate
from operational owners. Result: PASS_STATIC_SOURCE, not installed proof.

## C. Authority and ACLs

Independently reconstructed physical column grants: **1040**;
MISSING=0, EXTRA=0, DUPLICATE=0, GRANT_OPTION=0. No table-level grants or
direct domain DML grants to the seven owners. Lock-enabling UPDATE columns
are ordinary PostgreSQL privileges; reviewed bodies, not ACLs alone, restrict
their use to locking. ADMIN implicitly owns the fifteen new control/original
tables and its two functions; it is a trusted non-operational prerequisite.
Each function owner implicitly has EXECUTE/ownership rights. Those implicit
rights are not counted as one of the 32 explicit grants and cannot be revoked
as a substitute for role isolation. postgres/superuser bypass remains trusted.

Explicit function grants: **32**, exact signature/recipient missing=0, extra=0,
duplicates=0, PUBLIC_UNAUTHORIZED=0, SERVICE_DIRECT_PRIVATE_CAPABILITY=0.
Schema USAGE grants: **8**, missing=0, extra=0: public for all seven owners,
offline_crypto for V. Q's preinstalled private schema/HMAC/MAC32 path is a
separate approved prerequisite, not a ninth newly granted schema capability.

| Caller owner | Non-owner explicit dependencies in this source |
| --- | --- |
| A | Q, Z, pure V bridge, four frozen identity hash/fingerprint helpers (7) |
| V | native Ed25519, ADMIN original matcher, frozen V041 BEGIN/PERSIST (4) |
| I | six frozen V042 issuance functions (6) |
| E | P, Q, hash/grant fingerprint, V042 decision BEGIN/APPLY, intent/fingerprint/progress (9) |
| P | organization lock (1) |
| Z | five frozen authority intent/receipt/frame/text/instant helpers (5) |

A has no direct native schema/EXECUTE privilege. V has no SELECT on original
input; only its exact ADMIN-owned boolean matcher is granted. I/E have neither
original-table reads nor matcher/native EXECUTE. Z remains intent comparison;
Q remains the sole approved readiness/HMAC owner path. No service membership
or private capability grant is introduced. Declared private graph conforms;
installed/default/inherited ACL closure remains NOT_PROVEN. Overall transitive
review is PARTIAL because the wrong public names and missing adapter path
prevent complete contract closure, despite correct explicit private grants.

## D. Native crypto

Independent C inspection found OpenSSL d2i_PUBKEY/i2d_PUBKEY,
EVP_PKEY_ED25519, EVP_MD_CTX_new, EVP_DigestVerifyInit and EVP_DigestVerify;
no curve arithmetic, fallback or caller algorithm selector. Exact 44-byte SPKI
and 64-byte signature, complete DER consumption, canonical re-encode comparison,
and exact supplied message bytes are enforced. Only result1 returns true;
governed invalid-key/signature rejection returns false, structural input raises
22023, operational/internal failure raises XX000. All error queue entries are
examined for the approved operational classifications. No mutable global data,
filesystem/network call or secret persistence is added. timing_safe_equal32
matches its accepted `19131bb` baseline after line-ending normalization.

Rebuilt twice in pinned network-none scratch-only builder
`sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561`:
PostgreSQL18.4 / OpenSSL3.5.6. Candidate binary SHA256:
`5aeedcdb693442b7738b6f33604e059094f584af29d1879bf35482ca06ef63b5`.
Both builds match. 51 JCA/native acceptance decisions match; 50 exact taxonomy
matches, with the independently approved invalid-point classification difference.
Ten operational injections remain XX000; MAC32 equality/inequality regression
passes; ASAN/UBSAN bounded harness passes. OpenSSL itself is not instrumented.
Five exported symbols exactly match the allowlist; dependency/import inspection,
RELRO/BIND_NOW/non-executable stack pass. No extension installation occurred.

## E. Original signed input

The original relation has binding PK, required non-null canonical fields,
commitment check and header FK; the reciprocal deferred header FK requires
one original per binding at commit. Guard rejects UPDATE/DELETE; TRUNCATE
guard rejects bulk deletion. Required values are separately provisioned original
input, never self-derived from accepted artifact. S02 recomputes the six-field
canonical original and commitment/header agreement, compares exact signer key,
fingerprint and signature, and verifies canonical/JCA/native evidence.
The ADMIN matcher independently authenticates bound VERIFIER session and B4,
uses INTO STRICT cardinality, recomputes canonical bytes/hash/header agreement
and returns true only for all five exact caller signed fields. Missing/corrupt
original returns false; wrong session/scope/null is sanitized P0017.
S05/S06 require IS TRUE before frozen lookup/persistence. I/E use durable V
lineage followed by frozen revalidation; no caller truth flag, cached verification
boolean or raw original projection substitutes for that authority.

New focused executions: audit AA=true AB=false BA=false BB=true;
mutation AA=true AB=false BA=false BB=true. Both valid signatures are retained
test fixtures over the same manifest/plan. PASS_BOUNDED_SOURCE_AND_FOCUSED_RUNTIME.

## F. Transactions and locks

S01-S04 require read-only REPEATABLE READ/R, enforce live wall-clock read policy,
and have no DML/effect locks. S05-S18 require read-write READ COMMITTED with M
(S13's specified initial/retry exception). C precedes domain authority, ordering
lifecycle, pointer/current attempt, execution, relevant delivery/admission.
V/I delegated domain operations preserve frozen nested lock order. Actual writes
are limited to the control transitions listed in the independent per-function JSON.
No wrapper activates headers, changes generation, extends deadlines or records
ceremony success. S05 locks only; S06 writes receipts/progress only after original
comparison, native/frozen verification and final checks. S07/S09/S11 lock only;
S08/S10/S12 receipt/bookkeeping follows frozen success. S13 original retry does
not renew; S14 consumes once; S15 identical report preserves recorded time.
S16 locks admission before P, validates current credential/grant and immutable
V/I/delivery lineage, and preserves retry deadline. S17/S18 take admission before
P's organization/principal locks, then decision advisory/progress/sorted advisories;
the frozen domain functions reenter those locks. No static inversion found.

S17 is preparation/locks only; S18 rederives private facts and original snapshot,
rechecks commitment/current authority, invokes frozen APPLY and atomically consumes
admission, completes attempt, releases execution, requires reconciliation, leaves
ceremony NONE. Final wall-clock checks occur after frozen mutation and after
completion bookkeeping. Raised wrapper errors roll back the PL/pgSQL exception
block; trusted adapters must roll back the whole transaction. New focused run
proved savepoint rollback on injected late failure with stub frozen effects.
The supporting harness uses one READ COMMITTED connection/transaction for
S17/S18, but the actual new adapter path is absent (H02). SQL deliberately has
no new BEGIN/JCA provenance row; same-connection enforcement is the specified
trusted adapter duty. Mixed normal-runtime/offline barrier/deadlock evidence
and actual frozen rollback are deferred runtime obligations (M04), not source PASS.

## G. Frozen V041/V042 parity

All 42 frozen files equal accepted `19131bb9cd655312252c8c83f0f78e7c0742274f`
Git contents after canonical LF normalization. No frozen edit occurred.
Independent AST comparison proves normative tuples against actual frozen input/
output vectors for S05-S12 and S18, including 29/38 V inputs, 26/45 principal,
28/47 credential, 27/46 grant and 73 decision APPLY inputs. All fifteen actual
delegated call sites have exact arity, typed declarations and parameter order,
including original snapshot's nineteen expected S18 values. S17's actual FB
input30 and output33 fields were inspected; its retained twenty-field snapshot
is the governed subset, not the complete FB diagnostic projection.

BEGIN READY/ALREADY_APPLIED, V VERIFY_NEW/VERIFY_EXISTING and receipt
ACCEPTED/ALREADY_ACCEPTED/APPLIED/ALREADY_APPLIED classifications are consistent
at the frozen boundary; required nullable BEGIN diagnostics are preserved and
expected-snapshot/current-authority comparisons are retained. V041 requires
verified_at=recorded_at itself. Frozen receipts preserve original operation and
effect time on replay. Wrapper exceptions intentionally sanitize frozen failures
to P0017, except the specified decision replay route; this is not a new claim of
identical legacy adapter error taxonomy. S10's public wrapping is wrong (H03).

Classification: **PARTIAL**: metadata/order/type PASS, S10 public transport FAIL,
operational frozen SQL behavior **NOT_PROVABLE_WITHOUT_RUNTIME** on this evidence.
Mocks/JDBC witnesses prove supplied vectors, not frozen state transitions, signer
lock races, triggers, installed privileges, native-in-PG behavior or concurrency.

## H. Actual Kotlin/JDBC integration

Repository-wide Kotlin search found no production call to offline_preflight,
offline_begin_verification, offline_claim_attempt or offline_prepare_attested_decision.
PostgresAcceptedAttestationVerifier still binds29/38 scalar parameters to direct
V041 functions and reads named result columns. PostgresAttestedCommandAuthorityIssuer
binds26/45,28/47,27/46 scalar parameters to direct V042 functions and reads32/5
column tuples. PostgresTransactionIdentityWriter still directly calls FB30/FA73,
and PostgresCommandAuthorization reads raw credential/authority relations.
The governed service logins have only wrapper EXECUTE, so these calls cannot
operate under their approved ACL; adding legacy grants would widen authority.

Existing adapters preserve useful READ COMMITTED/rollback/JCA sequencing, but
none binds B/T/E or encodes/decodes the new opaque transports, obtains admission,
or implements the S17/S18 same-connection path. Merely renaming SQL is insufficient.
The new admission-backed actor/factory and four slot data-source integration
must be bounded against SPEC9/10/21.1/22.2 before implementation; this review
does not invent an actor from a UUID/boolean, broaden ACLs or redesign adapters.
**FAIL. Stop at the integration finding; no adapter modification authorized by
an assumed local correction is performed.** No new SQL authority gap is asserted.

## I. Migration safety

First effective statement is unconditional DO raising55000, before SET LOCAL,
role/default checks or DDL. It remains byte-for-byte unchanged in this review.
No effect can precede it. Source requires direct postgres session, PG18/UTF8,
safe public schema/default ACLs, separately provisioned ADMIN/native/private
crypto prerequisites and restricted owner roles. It creates owner roles before
their grants, control tables before column grants, original relation before
reciprocal FK/trigger, functions before ALTER OWNER/revokes, and referenced
frozen functions must already exist. Original/header circular obligation is
deferrable within the transaction. No provider/network/file operation, hidden
existing binding fixture or production policy insertion is introduced.
SET LOCAL and transactional PostgreSQL DDL/roles are compatible with a trusted
transactional Flyway migration; removing the fence cannot be justified by a
successful extracted-body harness. Full dependency/catalog/constraint/default
closure still requires the isolated migration rehearsal after source closure.
**Interlock removal readiness: HOLD** due to H01/H02/H03 and required medium
corrections. No authorized G3F.4 handoff is emitted as though this were PASS.

## J. Test independence and adversarial coverage

The 189 method count agrees with the retained successful full-suite log; five
final executor checks are historical successes. This review audited that suite,
not reran all189; it reran native51+faults/sanitizers, both original A/B paths
and the actual isolated I/E body harness. No redundant test-count inflation.

The V/I/E source checker imports generator WRAPPERS/TYPES and regenerates the
reference AST. Tests comparing source to that reference cannot detect shared
wrong function names/argument names. They detect mutations of selected guards,
not correctness of the shared reference. The observed H01/M01 passed those
checks. The S10 output golden is derived from the frozen five-field tuple rather
than the normative overriding outer envelope. The mutation harness explicitly
uses test_delivery's SECURITY DEFINER table read to supply S14's receipt UUID;
this convenience masks H03 and cannot exist as service authority in production.

Useful independent coverage includes original A/B, canonical/JVM bytes, native
malformation/operational faults, explicit column ACL negative grants, malformed
frames, wrong bound fields, receipt replay, grant/evidence drift and late rollback.
Important remaining gaps: cold S13 fresh creation with actual Q/HMAC; all18
wrappers' two-organization and every-null/cast matrix against real catalogs;
wrong-slot direct EXECUTE/default ACL/membership escalation under installed ACLs;
real frozen signer/receipt/replay states and partial failures; and mixed normal
runtime/offline lock barriers. Existing single-session mocks do not fill them.
M03 requires an independent manifest/output oracle before source reapproval;
M04 explicitly defers real operational/ACL/concurrency coverage to isolated runtime.

## Findings and required disposition

| ID | Severity | Exact location | Invariant / failure | Deterministic correction / new authority | Before rehearsal? |
| --- | --- | --- | --- | --- | --- |
| G3F3B-H01 | HIGH | V043:14379,15300; build_package_0090_issuance_source.py:12 | S11/S12 normative names absent; two unapproved alternatives. Correctly provisioned clients/catalog manifest cannot resolve required regprocedures. | Rename definitions/tooling to offline_begin_grant/offline_apply_grant, retain no aliases; existing exact SPEC authority suffices. Review evidence only here. | REQUIRED |
| G3F3B-H02 | HIGH | PostgresAcceptedAttestationVerifier.kt:146; PostgresAttestedCommandAuthorityIssuer.kt:213; PostgresTransactionIdentityWriter.kt:443; PostgresCommandAuthorization.kt:17 | Actual adapters use legacy scalar/raw-table contracts; governed wrapper-only logins cannot run the ceremony. UUID/boolean actor substitution or legacy grants would violate authority. | Not a local rename: bounded typed transport/admission/slot integration is needed. Record its exact scope under existing SPEC; any new factory/API authority boundary must be resolved before implementation. No authority broadening is inferred. | REQUIRED |
| G3F3B-H03 | HIGH | V043 offline_apply_initial_credential:14353,14372; build_package_0090_issuance_source.py:74-97; mutation harness test_delivery:137 | SPEC21.1:497 requires frozen_receipt + fresh UUID/NULL + execution/instance/delivery state. Actual S10 returns only frozen outcome/operation/intent/receipt/time. S14 requires server stage UUID not returned to caller. | Keep private durable receipt's frozen five fields; return the approved outer envelope. Fresh APPLIED exposes its UUID, ALREADY_APPLIED NULL/no permission; no service SELECT/helper added. Existing SPEC suffices. | REQUIRED |
| G3F3B-M01 | MEDIUM | V043 S06-S12/S16/S18 parameters; SPEC21.1 | Exact input names disagree (envelope/proof/verified request); named calls/catalog proargnames fail, even where positional types match. S11/S12's renamed definitions also need their correct request names. | Correct nine stages' names in definitions/generators/review expectations, preserving type vectors; no new authority. | REQUIRED |
| G3F3B-M02 | MEDIUM | Fifteen frozen call sites, independent JSON delegated_calls; SPEC21.1:285 | Internal calls omit explicit casts mandated by the manifest. Typed locals currently resolve exact frozen vectors, so no demonstrated overload exploit, but strict contract closure fails. | Add exact governed argument casts without changing values/vector; no new authority. | REQUIRED |
| G3F3B-M03 | MEDIUM | package_0090_verification_source.py:5-28; test_package_0090_executor_source.py; test_package_0090_issuance_source.py; mutation harness:137 | Generator/reference agreement falsely certifies wrong manifest and S10 flow; privileged fixture supplies missing service transport. | Independent normative names/modes/output comparison and unassisted S10-to-S14 receipt path evidence; do not count mirror tests as independent proof. Review extractor already reveals mismatch; existing authority suffices. | REQUIRED |
| G3F3B-M04 | MEDIUM | package_0090_mutation_isolated_review.py:166,236; verification isolated harness stubs; SPEC10/21.8 | Real frozen mutation semantics, effective installed ACL/defaults, cold claim and mixed-lock concurrency remain unproved. No source-determinable escalation/inversion inferred from this gap. | Actual frozen/native/ACL/all18 negative/replay/rollback/barrier matrix in disposable PG18.4 after required source closure. Runtime fixtures only; separately governed rehearsal authorization. | ACCEPTABLE TO VALIDATE IN ISOLATED RUNTIME |
| G3F3B-L01 | LOW | V043 header:1-9; older G3F.3B handoff | Header/handoff still describe earlier S01-S04/incomplete scope, confusing current review provenance. The execution fence is effective and must remain. | Update descriptive scope/evidence links after correction review; never change the fence merely to update comments. No new authority. | Documentation correction with closure |

No confirmed cross-organization access, direct service/private crypto elevation
or original-signature substitution was found in inspected source. That is not
a certification of the unexecuted installed system. BLOCKER=0 is a finding
classification, not permission to ignore the three HIGH findings.

## Exact next technical gate

`G3F.3B_SOURCE_FINDINGS_AND_ADAPTER_SCOPE_CLOSURE`.
Required handoff: correct H01/H03/M01/M02 under existing SQL contracts without
adding an alias/helper/grant; replace shared-reference claims with independent
manifest/output evidence; define the bounded adapter transport/admission scope
for H02 and determine whether any genuinely new design authority is necessary;
then independently review the corrected checkpoint. Maintain V043 interlock,
frozen V001-V042, physical1040 and private32/8 inventories throughout.

Only after HIGH=0 and required MEDIUM corrections are closed can a PASS prepare
the separately authorized `G3F.4_ISOLATED_POSTGRES18_REHEARSAL` environment,
provisioning/install/order/catalog/crypto/wrapper/lock/rollback handoff. This
review neither approves that gate nor removes the source fence.
