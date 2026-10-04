# Package 0090 S02 verification-path authority boundary

## Validated authority milestone

Branch: checkpoint/package-0090-cloud-handoff.
Authority commit: 7e5166e2cf2aba2dfb0456c487c83bf05fae83a1.
Fetch proved local=remote and WORKTREE=CLEAN immediately after that push.

All three preexisting substantive diff hunks were classified
EXPECTED_S02_AUTHORITY_AMENDMENT: ADR hunk +349, SPEC hunk +1172
(27 existing consumer rows), and SPEC hunk +2370. UNEXPECTED_SCOPE_COUNT=0.
The two preexisting script modifications had no textual diff against HEAD.
Corresponding audit/test expectations were updated to the approved consumer
scope. Only those four files entered the authority commit.

Consumer inventory, three read-source tests, source prerequisite gate and
git diff --check passed before commit. The normative physical set before/after
the amendment equals the actual V043 set: 1032; missing=0; extra=0.
New columns=0; new physical grants=0.

## Implementation analysis and exact new boundary

Work continued immediately into S02 producer and capability inspection.
PostgresOfflineFieldProofSupport.kt acceptedArtifact (lines 267-331) does not
return the signer join's eligibility alone. After the bound accepted count and
exact join, it parses canonical Ed25519 SPKI, constructs the validated proof,
compares canonical manifest/digest/preimage/signature/schema/window/recording
time, recomputes the accepted-proof fingerprint, verifies the Ed25519 signature,
and rejects a second joined row. accepted catches failures and returns false.

ApprovalGovernance.kt SignerPublicKeyInfo.parse uses JCA KeyFactory decoding and
canonical round-trip. ApprovalAttestationCanonicalCodec.kt
Ed25519ApprovalSignatureVerifier.verify uses JCA Signature over the exact
preimage. This is actual frozen behavior, not an inferred optional check.

SPEC21.1 closes S02's eleven output fields and seven count tags; it contains no
accepted proof snapshot or signature verification input/result transport. S03
separately has an accepted_snapshot and explicitly retains adapter JCA; that
transport is not S02 authority. SPEC23.1 grants only Q non-owner access to the
two approved crypto primitives (HMAC and the comparator); A is expressly
excluded. V001-V043 contain no Ed25519 verification function. Existing Z returns
only canonical authority intent/receipt matches, not signature validity.

The S02 signer-column amendment does not authorize a new verifier/helper,
function/schema EXECUTE grant, wider projection, client truth flag or retained
verification result. Implementing a new cryptographic routine inside S02 would
introduce an unreviewed cryptographic implementation rather than use the frozen
JCA verifier. No such routine was created.

Therefore full S02 acceptedArtifact parity cannot presently be implemented on
the approved closed surface. Neither eligible signer rows nor an accepted-proof
fingerprint replaces fresh signature verification. No SQL wrapper or denial
stub was added to manufacture closure. No S03 semantic change was made.

NEXT_GATE=G3F.3B_S02_ACCEPTED_ARTIFACT_VERIFICATION_PATH_AUTHORITY.
UNRESOLVED_AUTHORITY_BLOCKER_COUNT=1.

The technically determined handoff is a bounded contract resolution specifying
where the exact frozen acceptedArtifact canonical/SPKI/Ed25519 checks execute
and how their result participates in S02's output without trusting caller or
cached truth. It must specify exact owner/callable/transport authority, preserve
the current predicate and fail-closed/cardinality behavior, and resolve the
existing no-helper/no-new-grant/no-expanded-output constraints before code.
This is a security authority boundary, not an implementation choice for the CEO.
S03 and S05-S18 continuation remains conditional on S02 PASS, which is not claimed.

## Bounded negative evidence

The exact frozen producer signer SQL executes in disposable in-memory SQLite.
The eligible synthetic relation produces one row. Independent changes to key
state, fingerprint, lineage, public key, algorithm; authority state/fingerprint;
approval source/action/role; permission; and each of five verified-at window
boundaries produce zero rows. Foreign and absent organizations both produce
zero. Duplicating accepted, key or authority rows produces two, demonstrating
why the frozen single-row check cannot be replaced with EXISTS.

These are signer predicate/cardinality tests only. Synthetic rows are not signed
proofs. Full S02 negative tests, foreign-binding wrapper denial, admission audit,
JCA parity and PostgreSQL execution remain unvalidated because S02 is absent.
No current possession inference or raw metadata output is introduced.

V001-V042 and V043 source are unchanged; the interlock remains. No protected DB,
production policy, crypto installation, live production role, G3G, main push or
secret output was attempted. Public wrappers remain S01/S04 (2/18), executors 0.
