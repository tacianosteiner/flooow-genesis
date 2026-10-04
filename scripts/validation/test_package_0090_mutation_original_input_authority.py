import unittest
from package_0090_mutation_original_input_authority import audit

class MutableOriginalAuthorityTests(unittest.TestCase):
    def test_original_comparison_is_not_silently_widened(self):
        result=audit()
        self.assertEqual(len(result['approved_operational_expected_reads']),8)
        self.assertEqual(result['v_i_e_expected_reads'],[])
        self.assertFalse(result['authority_widened'])
    def test_r_is_not_used_to_authorize_mutation(self):
        result=audit()
        self.assertFalse(result['s02_available_to_mutable_guard'])
        self.assertTrue(result['native_validity_cannot_identify_registered_original'])
        self.assertFalse(result['implemented_s05_stub'])

if __name__=='__main__':unittest.main()
