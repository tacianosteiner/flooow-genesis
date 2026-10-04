# Package 0090 native Ed25519 source closure

## Current status - approved normalization supersedes the historical hold

Baseline: 2dd97572d2a8d17e0f993ff6f6c4d72b501e44f1. Fetch proved local=remote
and a clean checkpoint/package-0090-cloud-handoff before work.
The supplied invalid-key error closure explicitly approves acceptance semantics,
not provider exception taxonomy. JCA_PROVIDER_EXCEPTION_TAXONOMY_PARITY=NOT_REQUIRED;
ACCEPTED_ARTIFACT_DECISION_PARITY=REQUIRED; FINAL_DECISION_PARITY=PASS.
The known FF point is CRYPTOGRAPHIC_REJECTION_FALSE; both providers reject at
accepted(). This supersedes the historical error-contract hold below.

NATIVE_SOURCE_CLOSED=YES_BOUNDED_NOT_RUNTIME. All 51 vectors were rerun: 50
comparable results match, 51 acceptance decisions match, with no positive or
false-to-true divergence. All structural malformed vectors remain 22023 errors.
Eight fault-injection paths remain XX000, including context allocation,
initialization, unexpected negative/positive verification results, key parsing
allocation, both encoding failures and allocation on a zero verification result.
Fault substitutions exist solely in the test harness, never in deployable C.
ASAN/UBSAN and MAC32 equal/unequal regressions pass. Two clean PGXS builds have
identical binary SHA256. Exact export allowlist, imports, dependency and
RELRO/BIND_NOW/non-executable-stack evidence is regenerated in the JSON.

Extension SQL now binds exactly three unnamed mandatory bytea inputs to the
approved native symbol and immediately revokes PUBLIC privileges. Six binding
and adversarial source tests pass, alongside the 131 existing Package0090 tests.
ADR/SPEC record the approved 22023/false/true/XX000 contract and narrow V/A path.
No installation, PostgreSQL execution, runtime ACL assertion, migration or
production role/policy action occurred. Native/SQL closure is not installed
deployment proof. Exact deployable candidate hash is in the regenerated JSON.

NEXT_GATE=G3F.3B_INTERNAL_V_BRIDGE_AND_S02_IMPLEMENTATION.
UNRESOLVED_INVALID_KEY_ERROR_BLOCKER_COUNT=0.
Continue with the exact V-owned bridge and full S02 acceptedArtifact flow.
Historical observations below remain retained research evidence.

## Historical checkpoint - error-contract hold before normalization

Baseline fetch proved local HEAD = origin/checkpoint/package-0090-cloud-handoff =
778d2c0687395ca5865611e56b2ddc036b091c96 and a clean worktree.
The supplied technical security approval authorizes a thin OpenSSL Ed25519
adapter, but requires frozen JCA semantics and fail-closed malformed-key error
handling. This checkpoint records a reproducible experiment, not native source
closure, deployment approval, a runtime certificate, or S02 completion.

## Implemented candidate and bounded evidence

The existing native C package now contains a candidate
canonical_spki_ed25519_verify entry point. The existing timing_safe_equal32
function is unchanged. Extension SQL, control and Makefile are unchanged:
the candidate has no SQL binding or new EXECUTE/USAGE authority.
No V-owned bridge or S02 implementation has been added.

The candidate enforces 44-byte SPKI and 64-byte signature structure, parses
SubjectPublicKeyInfo with d2i_PUBKEY, requires EVP_PKEY_ED25519 and full input
consumption, and requires exact i2d_PUBKEY round-trip. It uses
EVP_DigestVerifyInit with a NULL digest followed by one-shot EVP_DigestVerify
over the exact supplied bytes, including empty messages. Structural errors
raise 22023; initialization and verification API results other than 0/1 raise XX000.
It introduces no handwritten curve arithmetic, fallback, alternate algorithm,
algorithm configuration, IO, secret persistence or mutable cryptographic state.

The network-disabled disposable builder is the existing
flooow-0090-crypto-builder:fe0425a2, resolved to its full image ID in the JSON.
It supplies PostgreSQL 18.4 and OpenSSL 3.5.6. PGXS compilation with
with_llvm=no succeeds using the existing visibility and no-LTO options.
Default make additionally requests missing clang-19 bitcode; LLVM is not
required for the governed shared-library build. No dependency was installed.

The export allowlist has exactly PostgreSQL module magic, the two function
entries and their two metadata entries. ELF dependency, imported-symbol,
RELRO, BIND_NOW and non-executable-stack evidence is recorded in the JSON.
The binary hash is regenerated there, for this candidate only; it does not
replace the previously approved comparator-only binary identity.

The harness includes the actual native source and mocks only PostgreSQL
argument/error transport. Java vectors call the actual compiled frozen Kotlin
SignerPublicKeyInfo and Ed25519ApprovalSignatureVerifier classes, not a
transcribed substitute verifier. The 51 deterministic vectors include all
required applicable cases, non-Ed25519 X25519, invalid bit-string padding,
and additional encoded-point/scalar inputs and 32 small-order message cases.
ASAN/UBSAN pass with leak detection over the wrapper/harness; the OpenSSL
shared library itself is not sanitizer-instrumented. Existing MAC32 equal
and unequal checks pass. No PostgreSQL execution/parity is claimed.

## Exact unresolved difference

For SPKI `302a300506032b6570032100` followed by 32 bytes of `ff`, a
64-byte `ff` signature and message `00010203ff00464c4f4f4f57`:

- Frozen SignerPublicKeyInfo.parse accepts the DER and canonical round-trip.
- Frozen JCA initVerify throws InvalidKeyException: "y value is too large".
- OpenSSL parses and round-trips the same DER, initializes verification,
  and EVP_DigestVerify returns 0 (candidate returns false).
- OpenSSL's public-key check also reports "Key is valid" for this input.

All 50 validly comparable vectors agree exactly. This invalid-key vector is
not counted as comparable boolean parity. All 51 vectors agree after applying
accepted()'s catch-failure-to-false semantics. There is no observed positive
acceptance divergence and no claim that OpenSSL produced a successful signature
verification for the invalid-key input.

Nevertheless, the primitive's invalid-key error classification differs from
the frozen verifier: it classifies this invalid key as an invalid signature.
The approval separately requires malformed-key/structural error handling and
frozen behavior. It does not explicitly authorize collapsing this key error
into a cryptographic false result at the primitive boundary. No such authority
is inferred from the matching downstream accepted() boolean.

The OpenSSL public-check experiment does not repair this classification.
Recreating JCA's encoded-point validation by handwritten curve logic would
violate the approved thin-adapter constraint. This checkpoint therefore stops
at the permitted security/semantic contradiction; it does not claim that all
possible OpenSSL APIs or every possible future solution have been exhausted.

NEXT_GATE=G3F.3B_ED25519_INVALID_KEY_ERROR_CONTRACT.
UNRESOLVED_BLOCKER_COUNT=1.
The next technically determined action is a bounded security contract resolution
for invalid encoded public points: establish an approved OpenSSL-only check
that reproduces the required error, or explicitly govern the primitive's
invalid-key false result while preserving accepted() rejection. No new caller
truth, cached verification, crypto grant or wider output is a resolution.
S02 and automatic S03/S05-S18 continuation remain conditional on source closure.

## Reproduction

Run from repository root:

```powershell
.\gradlew.bat :applications:marketplace-operations:classes --offline --no-daemon --console=plain
python scripts/validation/package_0090_ed25519_review.py
```

The existing Package0090 regression suite passed 131 tests using the already
available pinned pglast 7.10 at $env:TEMP/flooow-0090-parser. The initial default
Python invocation could not import that parser; setting PYTHONPATH to the
existing directory resolved it without installing a dependency. Gradle classes,
git diff --check, frozen migration integrity and source prerequisite checks
also passed. Full implementation/runtime closure remains HOLD.

The script resolves the existing image locally, mounts only a temporary review
directory and uses --network none. It does not install/load the extension,
start/connect to PostgreSQL, provision roles, or run migrations.

Reference API contracts:
[OpenSSL 3.5 Ed25519](https://docs.openssl.org/3.5/man7/EVP_SIGNATURE-ED25519/)
and [OpenSSL key checks](https://docs.openssl.org/3.5/man3/EVP_PKEY_check/).
Observed invalid-key behavior is local experimental evidence, not an inference
from these references.

V001-V043 and the V043 interlock are unchanged. No protected database mutation,
production policy, live role, G3G, main merge/push or secret output occurred.
Physical column grants remain 1032; new function/schema grants are zero.
Public wrappers remain S01/S04 (2/18); executor signatures remain 0.
