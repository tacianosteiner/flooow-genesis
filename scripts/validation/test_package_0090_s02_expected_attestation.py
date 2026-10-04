"""Actual frozen-JCA expected-input witness, without PostgreSQL execution."""
import unittest
from package_0090_s02_expected_attestation_audit import audit


class ExpectedAttestationBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=audit()
    def test_two_valid_originals_are_distinguished_by_frozen_accepted(self):
        witness=self.report['witness']
        self.assertEqual(witness['STORED_A_EXPECTED_A'],'true')
        self.assertEqual(witness['STORED_B_EXPECTED_B'],'true')
        self.assertEqual(witness['STORED_A_EXPECTED_B'],'false')
        self.assertEqual(witness['STORED_B_EXPECTED_A'],'false')
    def test_original_signed_inputs_have_same_bound_manifest_and_plan(self):
        self.assertEqual(self.report['witness']['CANONICAL_MANIFEST_EQUAL'],'true')
        self.assertEqual(self.report['witness']['PLAN_EQUAL'],'true')
        self.assertTrue(set(self.report['missing_expected_signed_fields']).isdisjoint(self.report['binding_columns']))
    def test_no_authority_widening_or_completion_claim(self):
        self.assertEqual(self.report['physical_column_grants'],1040)
        self.assertTrue(self.report['s02_implemented'])
        self.assertFalse(self.report['database_connection_attempted'])


if __name__=='__main__':unittest.main()
