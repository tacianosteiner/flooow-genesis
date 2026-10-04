# Package0090 fresh post-H02 G3F.3B source security review

Review date: 2026-10-04. Branch: `checkpoint/package-0090-cloud-handoff`.
Reviewed implementation commit: `796aa936b3be4db47360d7083bad383d9eb0793c`.
The implementation checkpoint was pushed/fetched before this fresh review.

G3F_3B_IMPLEMENTATION_SECURITY_REVIEW=PASS.
BLOCKER_COUNT=0; HIGH_COUNT=0; MEDIUM_COUNT=1; LOW_COUNT=0.
REQUIRED_PRE_REHEARSAL_MEDIUM_COUNT=0.
The one residual medium is M04=RUNTIME_VALIDATION_REQUIRED, explicitly allowed
at this source gate. This is not PostgreSQL installation/activation approval.

## Independently reconstructed evidence

The post-checkpoint SQL review re-parsed SPEC21.1/22.4 and actual SQL AST, not
generator maps. It re-established exact public names/arguments/types/returns,
owners/security/volatility/search_path, exact grants and all15 frozen delegated
argument-order/type/explicit-cast mappings. SQL source, the historical Phase A
evidence and V001-V042 remain unchanged. No prior PASS label establishes this
result. The AST review JSON records this newly reviewed source commit.

The independent adapter reviewer re-read SPEC and actual Kotlin statements and
frozen tuple declarations, then followed the executable main into its governed
factory/launcher and closed statement enum. It found18/18 exact input vectors
and zero reachable frozen/raw authorization calls. Negative tests separately
reject public-name, input-name/order/type/slot, legacy dependency and unchanged
decision-handoff mutations. These are independent contract checks, not
implementation-generator/reference agreement.

The fresh complete offline run passed194 tests in260.458 seconds. This includes
the retained191 suite plus3 new independent adapter-oracle test methods; subtest
mutations are not inflated into separate PASS counts. The separate Kotlin run
passed41 cases:20 actual governed adapter cases and21 existing offline launcher/
input regressions. Its recording JDBC executes the real new production launcher
with a real Ed25519 TEST signature, not a fake JCA-success callback. It asserts
all18 calls, slots, argument order, transaction policy, separate stage commits,
auditor rollback, buffer destruction and same-connection exact-envelope APPLY.
Mocks remain explicit and do not certify installed SQL or actual slot ACLs.

Evidence files:

- `PACKAGE-0090-H02-INDEPENDENT-SQL-REVIEW.json` — post-checkpoint AST/ACL review.
- `PACKAGE-0090-H02-INDEPENDENT-ADAPTER-REVIEW.json` — independent SPEC/Kotlin
  comparison and hashes of the reviewed operational sources.
- `PACKAGE-0090-H02-ADAPTER-TEST-RESULTS.json` — actual41 Kotlin test results.
- `PACKAGE-0090-H02-FULL-OFFLINE-TESTS.txt` — actual194-method offline run.
- `PACKAGE-0090-H02-ADAPTER-SCOPE.md` — content review, authority assessment,
  production sequencing, configuration, ownership, replay and error mapping.
- `PACKAGE-0090-G3F-3B-POST-H02-SECURITY-REVIEW.json` — fresh dispositions and
  exact limitations. Earlier HOLD reviews remain historical, not rewritten.

## Findings reassessed from source

H01: CLOSED. S11/S12 are exactly offline_begin_grant/offline_apply_grant in the
normative manifest and actual SQL; no legacy alias/compatibility overload.

H02: CLOSED at the implementation source gate. The executable constructs only
four governed pools and the governed launcher. It does not construct the old
verifier/issuer/writer/authorization/raw-auditor composition. Normal runtime
implementations and frozen functions remain internal existing dependencies.
No role, service identity, privilege, wrapper, persistence relation, receipt
system, caller authority field or trust/output boundary was added. Required B,
expected deployment/digests/policy bytes and slot credentials are existing
client deployment expectations; server wrappers retain bound identity and R/M
authority. The added credential bridge is pure reuse of the retained digest.

H03: CLOSED. Public S10 carries the original fresh stage receipt; durable frozen
five-field semantics remain untouched. The actual launcher decodes that outer
envelope and passes only its UUID into S14. ALREADY_APPLIED/NULL stops before
S14 or TTY. No privileged helper, raw SELECT, caller UUID or receipt renewal.

M01: CLOSED. Actual18 SQL AST contracts and18 actual JDBC vectors independently
match normative names/order/types; generic aliases are rejected.

M02: CLOSED. All15 actual frozen delegated sites have exact explicit governed
casts without value/order/function/signature change.

M03: CLOSED. Independent SPEC/actual-SQL-AST and SPEC/actual-Kotlin reviews do
not import WRAPPERS, TYPES or implementation-generator maps. The new production
S10 path is covered by unassisted caller transport and replay tests; committed
S10 goldens are an additional fixture, not the normative oracle. Historical
test_delivery evidence does not supply receipt identity or establish closure.

L01: CLOSED. The validated Phase A header remains unchanged and its execution
fence remains the first source control. New H02/fresh-review evidence is linked
through the new closure and handoff, without rewriting historical labels.

## Security and residual runtime boundary

Mutable pairs use one owned READ COMMITTED connection and transaction with
retained canonical/JCA/proof validation before APPLY. S17/S18 cannot cross
connections through the adapter API; direct S18 outside its internal sequence
is rejected. S16 constructs only a private admission handle, not an actor from
a UUID/boolean. All adapter-owned verifier/request/token buffers are erased
before writer entry; a recording driver asserts that order. SQL driver-owned
copies and deployment driver/proxy/server logging remain deployment controls.

S14 commits before one TTY invocation within its original server window, bounded
conservatively by monotonic elapsed time and the exact approved policy margin.
Ambiguous commit, replay, expired window and delivery failure do not retry or
permit subsequent grant/admission. JCA interruption/tampering rolls back; errors
reach the executable only as sanitized denial-or-ambiguity requiring inspection.

Auditor calls use one read-only REPEATABLE READ snapshot and rollback; complete
history/digest, counts, original artifact/JCA, exact command, JVM decision/intent
and evidence fingerprints are checked. Missing/inconsistent observations deny
or remain indeterminate. Local effect completion does not write or infer formal
administrative ceremony SUCCESS.

M04 remains open: real installed PG18 roles/ACLs/catalog/defaults, full frozen
operational semantics, real-driver/lock/concurrency/recovery/deployment-clone
and watchdog behavior need the separately authorized isolated rehearsal. The
source parser uses PostgreSQL17 grammar. Existing extracted-body harnesses use
explicit frozen stubs; they are not complete frozen execution certification.

V001-V042=UNCHANGED; V043_INTERLOCK=RETAINED; V043_EXECUTED=NO;
PROTECTED_DATABASE_CONNECTION=NO; PRODUCTION_PROVISIONING=NO; G3G=NO.
NEXT_GATE=G3F.4_ISOLATED_POSTGRES18_REHEARSAL. That gate was not executed.
