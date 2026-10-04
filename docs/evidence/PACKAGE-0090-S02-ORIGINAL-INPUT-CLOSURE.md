# Package 0090 — S02 original-input source closure

Authority: user approval on baseline `1817e5168e060987017a94a545f4c51f6f5b78a0`.

The private ADMIN-owned `public.offline_expected_signed_attestation` has eight
non-null fields and exactly eight A/S02 column reads. The independently supplied
original signing tuple is framed under
`FLOOOW/OFFLINE-FIELD-PROOF/EXPECTED-SIGNED-ATTESTATION/V1`, tags 1–6. INSERT
checks its canonical bytes and the bound manifest digest; constraints enforce
algorithm, UUID, hashes, signature length and commitment digest. UPDATE, DELETE
and TRUNCATE are rejected. A deferred reverse FK prevents committing a header
without the original commitment. Registration uses one trusted transaction and
plain INSERT for both records; duplicate registration has no overwrite path.

S02 preserves four public parameters and the declared eleven-field bytea
projection. Expected values come exclusively from the private original input.
It recomputes both encodings and hashes, compares all original fields exactly,
preserves the frozen signer joins and historical windows, recomputes the accepted
proof fingerprint, and freshly verifies using the approved V/native bridge.
Predicate exceptions become false. No original signature/key fields leave S02.

The exact frozen Kotlin accepted() witness and the actual generated SQL accepted
block with the native C verifier both pass the same A/B matrix: AA/BB true,
AB/BA false, same manifest and plan, both signatures cryptographically valid.
The disposable PostgreSQL 18.4 rehearsal is network-disabled and mounts only
temporary scratch. It executes focused predicate/constraint transports, **not
V043**, and provisions no production role/policy/crypto or protected data.
Required registration/input tampering negatives pass, including the failed
expected INSERT rolling back its header and the deferred FK rejecting an orphan.
The JSON report enumerates tested cases and limitations; the new goldens are
explicitly isolated test fixtures, generated from original Kotlin signed input
before construction of a stored row.

Frozen inspection requires fingerprints for valid prefixes of one, two and three
operations. The earlier Z source incorrectly required three in all cases and
required a credential on GRANT even though the frozen operation carries NULL.
Its two-boolean signature and authority remain unchanged. The source now checks
one-to-three bounded operations and the correct null-credential grant scope;
S02 independently proves exact prefix/cardinality before consuming these flags.
No credential verifier is projected to A. Runtime certification of the complete
wrapper guard/state machine and effective deployment ACL remains pending.

Inventory: 15 private control relations, **1,040 physical column grants**, 14
currently present explicit function EXECUTE grants and four schema USAGE grants.
The two added frozen A EXECUTEs are the already-authorized grant fingerprint and
its invoker hash dependency; the text[] signature is inventoried explicitly.
V001–V042 remain unchanged. The unconditional V043 execution interlock remains.
Historical HOLD reports are retained as history and superseded by this closure.

Next technically determined action: checkpoint S02 source, push/fetch the
checkpoint branch, then implement S03 and S05–S18 with remaining source guards,
transports/goldens and exact EXECUTE closure.
