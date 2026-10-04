import unittest
import package_0090_source_gate as gate
import build_package_0090_issuance_source as issuance
from package_0090_verification_source import check

class IssuanceSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(gate.ROOT/gate.V043).read_text()
        cls.spec=(gate.ROOT/gate.SPEC).read_text()
        cls.columns=gate.expected_column_grants(cls.spec)

    def review(self,source):
        statements,_=gate.parse(source)
        for stmt in statements:
            fn=stmt.get('CreateFunctionStmt')
            if fn and fn['funcname'][-1]['String']['sval'] in issuance.WRAPPERS.values():check(fn,self.columns,source,composition=issuance)

    def test_exact_issuance_composition(self):self.review(self.source)

    def test_durable_original_lineage_and_ack_are_mandatory(self):
        generated=issuance.build(self.source,self.spec)
        for old,new in [('slot_number=2','slot_number=3'),('snapshot.result_accepted_proof_fingerprint IS DISTINCT FROM verified_result_accepted_proof_fingerprint','false'),("delivery_record.state<>'DELIVERY_ACKNOWLEDGED'",'false'),("result.outcome<>'APPLIED' OR delivery_record.state<>'NOT_CREATED'",'false'),('delivery_record.fresh_applied_receipt_id IS DISTINCT FROM stage_receipt_id','false'),('verification_receipt.execution_id<>$7','false'),('codec_cursor<>pg_catalog.octet_length(verification_receipt.frozen_receipt)','false')]:
            with self.subTest(old=old):
                self.assertIn(old,generated)
                with self.assertRaises(ValueError):self.review(self.source.replace(generated,generated.replace(old,new)))

    def test_issuer_has_no_original_or_native_dependency(self):
        generated=issuance.build(self.source,self.spec)
        for forbidden in ['offline_expected_signed_attestation','offline_internal_matches_original_signed_attestation','offline_internal_canonical_spki_ed25519_verify','offline_crypto.']:
            self.assertNotIn(forbidden,generated)

if __name__=='__main__':unittest.main()
