import unittest
import package_0090_source_gate as gate
from build_package_0090_verification_source import build,WRAPPERS
from package_0090_verification_source import check

class VerificationSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig')
        cls.spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')
        cls.expected=gate.expected_column_grants(cls.spec)

    def review(self,source):
        statements,_=gate.parse(source)
        for statement in statements:
            fn=statement.get('CreateFunctionStmt')
            if fn and fn['funcname'][-1]['String']['sval'] in WRAPPERS.values():check(fn,self.expected,source)

    def test_exact_source(self):self.review(self.source)

    def test_required_guard_and_codec_changes_rejected(self):
        generated=build(self.source,self.spec)
        for old,new in [('original_match IS NOT TRUE','false'),('slot_number=1','slot_number=3'),("current_setting('transaction_read_only') <> 'off'",'false'),('execution_record.possession_digest <> pg_catalog.sha256($9)','false'),('final_execution_record.expires_at IS DISTINCT FROM execution_record.expires_at','false'),('codec_cursor<>pg_catalog.octet_length($10)','false'),('result.result_organization_id<>header_record.organization_id','false'),('public.offline_internal_canonical_spki_ed25519_verify(snapshot.result_subject_public_key_info_der,snapshot.result_canonical_signature_preimage_bytes,input_p_signature_bytes) IS NOT TRUE','false')]:
            with self.subTest(old=old):
                self.assertIn(old,generated)
                with self.assertRaises(ValueError):self.review(self.source.replace(generated,generated.replace(old,new)))

    def test_actual_wrappers_native_and_independent_codecs(self):
        from package_0090_verification_isolated_review import review
        result=review()
        self.assertEqual(result['status'],'PASS_ISOLATED_WRAPPERS_STUB_FROZEN_TRANSPORTS')
        self.assertIn('POST_FROZEN_EXPIRY_ROLLS_BACK_EFFECT',result['negatives'])

if __name__=='__main__':unittest.main()
