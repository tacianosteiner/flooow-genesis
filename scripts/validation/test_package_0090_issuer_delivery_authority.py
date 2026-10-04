import unittest
from package_0090_issuer_delivery_authority import audit,FIELDS

class IssuerDeliveryAuthorityTests(unittest.TestCase):
    def test_existing_i5_and_physical_grants_are_aligned(self):
        result=audit()
        self.assertTrue(result['physical_i_select_exists'])
        self.assertTrue(result['authorized_s11_s12_consumer'])
        self.assertFalse(result['authority_widened'])

    def test_handoff_has_no_new_column_or_public_surface(self):
        result=audit()['selected_handoff']
        self.assertEqual(result['fields'],list(FIELDS))
        self.assertEqual(result['new_column_grants'],0)
        self.assertEqual(result['new_helpers'],0)
        self.assertEqual(result['new_public_signatures'],0)

if __name__=='__main__':unittest.main()
