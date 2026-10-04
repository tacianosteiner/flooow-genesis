import unittest
import package_0090_source_gate as gate
from build_package_0090_original_match_source import NAME, build
from package_0090_original_match_source import check

class OriginalMatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig')

    def review(self,source):
        statements,_=gate.parse(source)
        fn=next(s['CreateFunctionStmt'] for s in statements if s.get('CreateFunctionStmt',{}).get('funcname')==[{'String':{'sval':'public'}},{'String':{'sval':NAME}}])
        return check(fn,source)

    def test_exact_source(self):self.review(self.source)

    def test_identity_and_comparison_tampering_rejected(self):
        original=build(self.source)
        for old,new in [('slot_number=1','slot_number=3'),('SESSION_USER','CURRENT_USER'),('INTO STRICT original_record','INTO original_record'),('original_record.signature_bytes=$9','true'),('original_record.signer_key_id=$7','true'),('original_record.signer_key_fingerprint=$8','true'),('original_record.manifest_digest=$5','true'),('original_record.algorithm_id=$6','true'),('original_record.commitment_digest=pg_catalog.sha256(canonical_bytes)','true'),('original_record.canonical_expected_attestation=canonical_bytes','true'),('RETURN false','RETURN true'),('STABLE SECURITY DEFINER','VOLATILE SECURITY DEFINER')]:
            with self.subTest(old=old):
                self.assertIn(old,original)
                with self.assertRaises(ValueError):self.review(self.source.replace(original,original.replace(old,new)))

    def test_acl_tampering_rejected(self):
        for recipient in ['PUBLIC','flooow_offline_audit_owner','flooow_offline_issuance_owner','flooow_offline_execution_owner']:
            with self.subTest(recipient=recipient):
                # Add an unauthorized grant: exact inventory must reject every role.
                from build_package_0090_original_match_source import TYPES
                extra='\nGRANT EXECUTE ON FUNCTION public.'+NAME+'('+','.join('pg_catalog.'+t for t in TYPES)+') TO '+recipient+';'
                import package_0090_capability_source as capability
                with self.assertRaises(ValueError):
                    bad,_=gate.parse(self.source+extra)
                    capability.check(bad,gate.expected_column_grants((gate.ROOT/gate.SPEC).read_text()),self.source+extra)

    def test_isolated_actual_helper(self):
        from package_0090_original_match_isolated_review import review
        result=review()
        self.assertEqual(result['matrix'],{'original_A_caller_A':True,'original_A_caller_B':False,'original_B_caller_A':False,'original_B_caller_B':True})
        self.assertFalse(result['protected_database_connection'])

if __name__=='__main__':unittest.main()
