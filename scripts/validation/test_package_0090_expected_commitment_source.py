"""Adversarial original-input capability checks, plus isolated real SQL witness."""
import unittest
import package_0090_source_gate as gate
from package_0090_s02_isolated_review import review

class ExpectedCommitmentSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig')
        cls.spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')
    def reject(self,before,after):
        self.assertIn(before,self.source)
        with self.assertRaises(ValueError):gate.prerequisite_checks(self.source.replace(before,after,1),self.spec)
    def test_no_orphan_header(self):
        self.reject('REFERENCES public.offline_expected_signed_attestation(binding_id)\n    DEFERRABLE INITIALLY DEFERRED','REFERENCES public.offline_expected_signed_attestation(binding_id)\n    DEFERRABLE INITIALLY IMMEDIATE')
    def test_no_commitment_overwrite(self):
        self.reject("IF TG_OP<>'INSERT'", "IF TG_OP='DELETE'")
    def test_no_mutable_header(self):
        self.reject('offline_header_original_input_immutable BEFORE UPDATE OR DELETE','offline_header_original_input_immutable BEFORE DELETE')
    def test_no_truncate_bypass(self):
        self.reject('offline_expected_original_input_no_truncate BEFORE TRUNCATE','offline_expected_original_input_no_truncate BEFORE INSERT')
    def test_canonical_encoding_not_digest_only(self):
        self.reject('NEW.canonical_expected_attestation IS DISTINCT FROM','NEW.commitment_digest IS DISTINCT FROM')
    def test_no_unreviewed_trigger(self):
        with self.assertRaises(ValueError):gate.prerequisite_checks(self.source+'\nCREATE TRIGGER extra AFTER INSERT ON public.offline_expected_signed_attestation FOR EACH ROW EXECUTE FUNCTION public.offline_internal_expected_attestation_guard();',self.spec)
    def test_no_original_input_write_for_a(self):
        with self.assertRaises(ValueError):gate.prerequisite_checks(self.source+'\nGRANT UPDATE(signature_bytes) ON public.offline_expected_signed_attestation TO flooow_offline_audit_owner;',self.spec)
    def test_no_self_expected_signature(self):
        self.reject('accepted_record.signature_bytes=expected_record.signature_bytes','accepted_record.signature_bytes=accepted_record.signature_bytes')
    def test_no_self_expected_key(self):
        self.reject('accepted_record.signer_key_id=expected_record.signer_key_id','accepted_record.signer_key_id=accepted_record.signer_key_id')
    def test_no_crypto_reuse(self):
        self.reject('AND public.offline_internal_canonical_spki_ed25519_verify(', 'AND false OR public.offline_internal_canonical_spki_ed25519_verify(')
    def test_no_error_acceptance(self):
        self.reject('        accepted_ok := false;\n    END;', '        accepted_ok := true;\n    END;')
    def test_no_raw_expected_projection(self):
        self.reject('RETURN output_bytes;', 'RETURN expected_record.signature_bytes;')

class IsolatedExpectedCommitmentTests(unittest.TestCase):
    def test_real_postgres_original_input_and_native_matrix(self):
        report=review()
        self.assertEqual(report['status'],'PASS')
        self.assertEqual(report['ab_matrix'],{'expected_A_stored_A':True,'expected_A_stored_B':False,'expected_B_stored_A':False,'expected_B_stored_B':True})
        self.assertTrue(report['atomic_rollback'])
        self.assertFalse(report['v043_executed'])
        self.assertFalse(report['protected_database_connection'])

if __name__=='__main__':unittest.main()
