"""Apply the user's bounded expected-original-input authority to repository source."""
import package_0090_source_gate as gate
import build_package_0090_expected_attestation_source as expected
import build_package_0090_q_source as q
import build_package_0090_z_source as z

AMENDMENT = '''

## Independent original signed-attestation commitment approval — 2026-10-03

Authority: FLOOOW PACKAGE 0090 G3F.3B EXPECTED SIGNED ATTESTATION BINDING
AUTHORITY, baseline 1817e5168e060987017a94a545f4c51f6f5b78a0.
The public S02 four-input signature, output and 38-tag binding remain unchanged.
ADMIN owns the additional private public.offline_expected_signed_attestation
relation. It has exactly the eight non-null fields enumerated below; canonical
bytes use bytea. Tags 1..6 are binding UUID, manifest lowerhex64, algorithm,
signer UUID, signer fingerprint lowerhex64, and signature bytes, in that order,
under FLOOOW/OFFLINE-FIELD-PROOF/EXPECTED-SIGNED-ATTESTATION/V1.
Canonical framing uses the existing tagged framing and required presence bytes.
Ed25519 is mandatory, signer UUID is non-NIL, signature length is exactly 64,
and commitment_digest is SHA-256 of the exact canonical bytes.

Trusted ADMIN registration canonicalizes the original manifest, computes its
digest and constructs the expected tuple from the SAME independently supplied
original SignedApprovalAttestation. It inserts header then expected tuple in one
transaction. The existing forward FK and a DEFERRABLE INITIALLY DEFERRED reverse
FK require both or neither at commit; an expected insert failure requires the
registration transaction to roll back. Plain INSERT rejects duplicates. Neither
accepted rows, signer tables, reconciliation, snapshots nor S02 callers supply
the expected values. No repair or overwrite registration path is approved.

The narrowly required ADMIN-owned trigger function
public.offline_internal_expected_attestation_guard() validates the original
tuple against the header digest and exact canonical encoding before INSERT.
It rejects UPDATE/DELETE on either immutable input relation and statement-level
TRUNCATE, including privileged administrative data writes. As with all PostgreSQL
guards, trusted deployment superusers can alter DDL; that authority is outside
operational capabilities. PUBLIC function EXECUTE is revoked and no non-owner
EXECUTE is granted. Its only consumer is the four exact input-guard triggers.
This requirement narrowly supersedes section 24.2's no-ADMIN-function statement;
it adds no service authority, registration wrapper or operational execution.

A reads precisely these eight columns for S02_ONLY,
EXPECTED_ORIGINAL_SIGNED_ATTESTATION_COMPARISON, PRIVATE_PREDICATES_ONLY.
No expected fields are returned; no direct service/PUBLIC access or A write/lock
authority is granted. S02 recomputes the encoding and digest, compares expected
manifest/algorithm/key/fingerprint/signature exactly, builds the preimage from
the expected key tuple, freshly verifies Ed25519 and recomputes the accepted
proof fingerprint while preserving all frozen signer/window/cardinality checks
and accepted() error-to-false behavior. Source evidence does not certify runtime.

| OWNER | RELATION | COLUMN | PRIVILEGE_CLASS | CONSUMER / EXACT_QUERY_OR_INTERNAL_BLOCK | ENTRYPOINT | WHY_REQUIRED | CAN_REMOVE | TRANSITIVE_CAPABILITY |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
'''

def main():
    path=gate.ROOT/gate.SPEC
    spec=path.read_text(encoding='utf-8-sig')
    if '## Independent original signed-attestation commitment approval' not in spec:
        spec=spec.replace('- public.offline_binding_header\n','- public.offline_binding_header\n- public.offline_expected_signed_attestation\n',1)
        spec+=AMENDMENT+''.join(f'| A | public.offline_expected_signed_attestation | {field} | READ_PRIVILEGE | S02_ONLY expected-original comparison | S02 | Original independent signed input | NO | PRIVATE_PREDICATES_ONLY |\n' for field in expected.FIELDS)
        path.write_text(spec,encoding='utf-8')
        adr=gate.ROOT/'docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md'
        adr.write_text(adr.read_text(encoding='utf-8-sig')+AMENDMENT.split('| OWNER |')[0],encoding='utf-8')
    expected.install()
    source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig')
    z_start=source.index('-- Internal Z:')
    z_last='GRANT EXECUTE ON FUNCTION public.s2a_v042_instant(pg_catalog.timestamptz) TO flooow_offline_intent_audit_owner;'
    z_end=source.index(z_last,z_start)+len(z_last)
    source=source[:z_start]+z.build(source).rstrip()+source[z_end:]
    start=source.index('-- Internal Q:')
    end=source.index('-- Approved V Ed25519 bridge:')
    source=source[:start]+q.build(source,spec)+'\n\n'+source[end:]
    (gate.ROOT/gate.V043).write_text(source,encoding='utf-8')

if __name__=='__main__':main()
