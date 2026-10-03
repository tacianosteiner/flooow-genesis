# Package 0090 approved test policy checkpoint

Date: 2026-10-03 (America/Sao_Paulo).
Branch: checkpoint/package-0090-cloud-handoff.

Historical policy-only checkpoint. The subsequently authorized complete retained
normative evidence fixture resolves the information gap below; see
[normative evidence closure](PACKAGE-0090-G3F-3B-NORMATIVE-EVIDENCE-CLOSURE.md).
It is no longer an approval boundary. Remaining source work is recorded in
[internal P review](PACKAGE-0090-G3F-3B-INTERNAL-P-SOURCE-REVIEW.md).

FIXTURE_APPROVAL_RECORDED=YES
FIXTURE_POLICY_CLOSED=YES_TEST_ONLY
POLICY_VERSION=fixture-1
TAG28_US=1000000
TAG29_US=2000000
CANONICAL_POLICY_FIELD_COUNT=29
CODEC_GOLDENS=POLICY_REFERENCE_JVM_PASS_DEPENDENT_GOLDENS_HOLD
POLICY_SHA256=e840fcadac2d5198a91cdb7b2345a31d4776cb3ead6e8b697391a4461a1a253d
PACKAGE_0090_WRAPPER_IMPLEMENTED=NO
EXECUTOR_SIGNATURE_IMPLEMENTED=0_OF_6
EXECUTE_ACL_REVIEW=HOLD_NOT_IMPLEMENTED
STATIC_SQL_CONTRACT=PREREQUISITES_PASS_FULL_CLOSURE_HOLD
SECURITY_DEFINER_REVIEW=HOLD_NOT_IMPLEMENTED
MIGRATION_SAFETY_REVIEW=INTERLOCK_AND_FROZEN_CHAIN_PASS_FULL_REVIEW_HOLD
TESTS=32_PASS_OFFLINE_ONLY
UNRESOLVED_BLOCKER_COUNT=4
PROTECTED_DATABASE_MUTATION=NO
DATABASE_CONNECTION_ATTEMPTED=NO
REAL_FIELD_PROOF=HOLD
NEXT_GATE=G3F.3B_COMPLETE_NORMATIVE_EVIDENCE_FIXTURE

The approval is recorded in ADR/SPEC without changing other normative contracts.
The complete29-field policy is frozen in FIXTURE-001.json, including every
actual/maximum pair and full canonical hex. Python struct encoding and a separate
Java DataOutputStream program independently construct all bytes and SHA-256.
The Java encoder consumes neither Python output nor the JSON golden. Tests compare
both complete outputs and the committed fixture, check all numeric mutations,
reject nonpositive/noninteger/overflow/above-max values, legacy27-field frames,
null/malformed/truncated/trailing/tag-order input and non-NFC version text.
This is independent implementation agreement, not an external reviewer approval,
runtime expiry proof, signature proof or production policy authority.

## Newly identified normative fixture information gap

SPEC21.2 VECTOR_1 says its evidence_binding_fingerprint is the output of the
frozen public.s2a_v041_evidence_fingerprint and that no unspecified manifest
field remains. Source inspection disproves completeness of its input fixture:
V041 lines485-498 include selected ML/Omie evidence in the hash preimage, beyond
the six stated function arguments. The function is a catalog/data query, not a
pure hash of those six arguments. The normative VECTOR_1 supplies neither the
underlying evidence rows nor an approved retained evidence-binding preimage.

These selected values are still unspecified:

- ML input progress version, record ordinal, external order ID, currency and
  promotion outcome (PROMOTED versus DUPLICATE).
- Omie input progress version, record ordinal, nullable currency, semantic
  fingerprint version/value and selected civil provider revision.

The frozen function also requires complete promotion/registry/source joins,
Omie base/V3 rows, page-commit counts, connector progress, latest-revision
selection and absence of equal-revision conflicts. Supplying only UUID6/10/8/9
and the two references cannot determine that output. Different admissible source
evidence changes the evidence fingerprint, frozen manifest hash and binding
fingerprint while preserving every currently stated VECTOR_1 field. The policy
digest is uniquely determined and is closed independently of this gap.

No evidence row, fingerprint, zero value, synthetic signature, full manifest
digest, binding digest or authenticated receipt is invented here. The previously
stated full-fixture completeness claim cannot be promoted into evidence. The
current authority permits ADR/SPEC edits **only** to record this TTL fixture
approval/provenance; changing VECTOR_1's normative evidence semantics would be a
new contract amendment outside that edit scope. This is the new boundary, not a
request for the CEO to choose database values or algorithms.

## Exact technical handoff

The independent technical fixture process must close VECTOR_1 with either its
complete retained canonical evidence fixture (including the selected values and
integrity/selection facts above) or a specifically approved evidence-binding
preimage tied to that fixture. Preserve the existing UUIDs, references, windows,
manifest fields and policy_version=fixture-1. Record the data and provenance as
test-only evidence; do not retrieve protected live data or change V041/V042.
Validate its frozen-codec parity, then derive the exact22-field manifest and
38-field binding for VECTOR_1/2/3 and continue the approved implementation.
This handoff selects the missing evidence requirement; it presents no CEO
implementation menu and requests no production policy.

## Source and rehearsal limits

V043 is unchanged in this checkpoint and retains its unconditional execution
interlock. Source checks still parse1,094 SQL statements and11 PL/pgSQL blocks,
verify14 controls and1,020 exact physical column grants, and preserve all42
frozen migrations. No21-function/18-signature implementation or runtime test is
claimed. Four source closure categories remain: wrappers, guards, full codecs/
goldens and EXECUTE ACLs. The new information gap belongs to the existing full
codec/golden category; it is not counted twice.

The existing isolated rehearsal preparation remains valid with the TTL approval
entry condition now satisfied. Full source closure, complete dependent goldens,
separate bounded isolated execution authority and deployment prerequisites are
still absent. R01-R10 were not executed. No database connection, policy seed,
live role, secret, G3G, merge or main push occurred.

Reproduce offline validation:

```powershell
python -m unittest discover -s scripts/validation -p test_package_0090_policy_fixture.py -v
python -c "import sys, unittest; sys.path[:0]=[r'C:\Users\xmz_r\AppData\Local\Temp\flooow-0090-parser', 'scripts/validation']; r=unittest.TextTestRunner().run(unittest.defaultTestLoader.discover('scripts/validation', pattern='test_package_0090*.py')); sys.exit(not r.wasSuccessful())"
python scripts/validation/package_0090_source_gate.py --parser-path C:/Users/xmz_r/AppData/Local/Temp/flooow-0090-parser
```

Parser remains pinned pglast7.10 (PG17 grammar), not PG18 execution proof.
Java source-file execution requires the installed JDK21; no package/application
dependency or production build configuration was changed.
