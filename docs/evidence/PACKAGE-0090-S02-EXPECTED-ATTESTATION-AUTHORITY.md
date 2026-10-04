# Package 0090 V bridge closure and S02 expected signed-input boundary

## Current validated milestones

Branch: checkpoint/package-0090-cloud-handoff.
Native source closure checkpoint: 8988a15ade44ac8a716971f79025fb34c4723a76,
pushed/fetched with local=remote and clean worktree before continuation.
The invalid-key error-contract blocker is closed under the explicit normalization.
All 51 native/JCA acceptance decisions agree; all 50 comparable results agree;
the FF point is false. Ten operational fault injections preserve XX000,
including queued allocation errors and encoding/internal invariants.
Native SQL binding and reproducible candidate binary review are closed for
source only, as recorded in PACKAGE-0090-ED25519-NATIVE-REVIEW.json.

The V bridge is implemented in V043 source. Its exact catalog prerequisite
requires the preinstalled Ed25519 function to have D ownership, the approved
extension/symbol/module/properties and D-only ACL before new grants. Existing
crypto inspection is retained. V043 source then grants only V private-schema
USAGE and native EXECUTE, never general crypto access or corrective ACL repair.
The bridge is V-owned IMMUTABLE STRICT PARALLEL SAFE SECURITY DEFINER with fixed
search_path=pg_catalog,pg_temp; it forwards exactly $1/$2/$3 to the native
primitive. Only A has non-owner bridge EXECUTE. A gets no private-schema USAGE,
direct native EXECUTE or key-material authority. PUBLIC/services get none.
The existing public-schema USAGE for A is sufficient for bridge resolution;
the bridge's native resolution occurs as V. Installed runtime proof is separate.

The capability review now explicitly closes the two new EXECUTE grants and
one new schema-USAGE grant, independently from table-column grants (1032).
Q's named function catalog universe includes the bridge and the Ed25519 native
primitive, so their ownership/EXECUTE paths participate in its ACL digest.
Q's crypto calls and HMAC/comparator grants remain unchanged. Eight bridge
adversarial tests reject A-native access, A-private-USAGE, PUBLIC/service helper
grants, changed arguments, invoker mode, mutable search path, missing native
prerequisites and error-to-true behavior. Source prerequisite checks pass.
The complete present-source inventory records 12 EXECUTE grant statements and
four schema-USAGE grant statements separately from 1032 physical column grants;
preinstalled Q dependencies and implicit function owners are recorded separately.
This is not complete installed/transitive ACL proof for future wrappers.
The Package0090 offline suite passes 148 tests; Gradle classes, native safety
review, frozen V001-V042 integrity, source prerequisite gate and diff checks pass.

## Next genuine contract contradiction: expected signed attestation is absent

Frozen PostgresOfflineFieldProofReconciler.acceptedArtifact accepts an input
containing SignedApprovalAttestation. It compares the stored proof against that
independent original input, including:

- proof.algorithmId == signed.algorithmId;
- proof.signerKeyId == signed.signerKeyId;
- proof.signerKeyFingerprint == signed.signerKeyFingerprint;
- publicKey.fingerprint() == signed.signerKeyFingerprint;
- proof.signatureBytes() equals signed.signatureBytes();
- canonical preimage constructed from the original signed key ID/fingerprint.

S02 has exactly four public inputs: binding ID, plan fingerprint, incarnation
and surface. SPEC4's immutable 38-tag binding and the physical binding header
retain the canonical manifest and its digest, plan, target and identity slots.
They retain no independently expected signer key ID/fingerprint/signature.
The canonical manifest codec excludes signing identity/signature; its digest
cannot commit those absent bytes. Algorithm Ed25519 is statically enforceable,
but the key ID/fingerprint/signature of the original bundle are not derivable
from that algorithm or the manifest.

## Controlled witness using actual frozen code

The Java witness signs the same canonical manifest with two public RFC8032
test keys and their respective correct canonical preimages. It calls the actual
compiled frozen private accepted() method through reflection. Only JDBC
transport is mocked; no database or alternative accepted verifier is used.
The mock supplies one accepted row and one eligible joined proof; independent
existing signer-query/cardinality tests retain their separate relational scope.

| Stored accepted artifact | Independent expected original A | Independent expected original B |
| --- | --- | --- |
| A | true | false |
| B | false | true |

Both diagonal cases run the frozen canonical/proof-fingerprint/JCA verification
successfully. Both off-diagonal cases reject. The canonical manifests and plans
are identical, so all 38 binding fields, retained manifest bytes and four S02
inputs can be identical while the frozen expected-input decision differs for
the same stored row. The JSON records source hashes, exact comparisons, header
columns, tag rows and actual witness outputs. This is an information gap, not
provider exception taxonomy or cryptographic verification failure.

A S02 routine reading the same DB/header and receiving the same four inputs
cannot reproduce both decisions without an independent commitment identifying
the original signed input. Reusing the stored row's signer/signature as its own
expected input would remove the frozen comparisons. Fresh native verification
and accepted-proof recomputation prove the stored artifact's internal validity;
they do not bind it to the missing original signed input. S03's separately
authorized accepted snapshot/JVM transport does not add such authority to S02.

## Decision and exact next action

S02 remains absent; no denial stub, incomplete wrapper, caller truth flag,
cached verification result, raw signing output or new data-column grant was
introduced. Its public signature is unchanged. No completed S02 parity claim
is made; automatic S03/S05-S18 continuation remains conditional on S02 PASS.

NEXT_GATE=G3F.3B_S02_EXPECTED_SIGNED_ATTESTATION_BINDING.
UNRESOLVED_AUTHORITY_BLOCKER_COUNT=1.

The technically determined resolution is a bounded normative independent
original signed-attestation commitment retained by trusted binding registration
and privately compared by S02 before fresh verification. Its exact canonical
bytes, immutable binding relationship, provenance and minimal A read authority
must be defined under governance. The approved contract retains
the four public parameters, 38-field binding and existing data-column grants;
it does not authorize inventing a new stored commitment, grant or fingerprint
version. No such schema/codec/authority amendment is inferred here.

## Reproduction and limits

```powershell
.\gradlew.bat :applications:command-authority-ceremony:classes --offline --no-daemon --console=plain
$env:PYTHONPATH="$env:TEMP\flooow-0090-parser;scripts/validation"
python scripts/validation/package_0090_s02_expected_attestation_audit.py
python -m unittest discover -s scripts/validation -p 'test_package_0090*.py'
```

The parser is the existing pinned pglast 7.10. No dependency installation,
protected PostgreSQL connection, V043 execution/interlock removal, V001-V042
change, protected runtime install, production role/policy, G3G or main push
occurred. Public wrappers remain S01/S04 (2/18); executor signatures remain 0.
All evidence is bounded source/mock/native review; installed ACL and PostgreSQL
runtime parity remain unproven.
