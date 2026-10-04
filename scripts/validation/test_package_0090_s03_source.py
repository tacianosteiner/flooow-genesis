"""S03 corruption/consumer/projection source boundaries."""
import unittest
import package_0090_source_gate as gate

class ReconciliationSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig');cls.spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')
    def reject(self,before,after):
        prefix,body=self.source.split('AS $offline_s03$',1)
        self.assertIn(before,body)
        with self.assertRaises(ValueError):gate.prerequisite_checks(prefix+'AS $offline_s03$'+body.replace(before,after,1),self.spec)
    def test_current_exact_private_reconciliation(self):
        report=gate.prerequisite_checks(self.source,self.spec)
        self.assertEqual(report['s03_expected_input_consumption'],'DELEGATED_TO_S02')
    def test_no_durable_exact_flag(self):self.reject("domain_projection='DECISION_HEAD_PRESENT'","true")
    def test_no_authority_fingerprint_skip(self):self.reject('AND fingerprint_record.intent_matches AND fingerprint_record.receipt_matches','AND true')
    def test_no_missing_evidence_exactness(self):self.reject('AND head_matches AND decision_matches AND evidence_matches IS TRUE','AND head_matches AND decision_matches')
    def test_no_duplicate_evidence_snapshot(self):self.reject('IF evidence_record.evidence_cardinality=1 AND evidence_record.marketplace_key IS NOT NULL THEN','IF evidence_record.marketplace_key IS NOT NULL THEN')
    def test_no_private_expected_read(self):self.reject('inspect_bytes := public.offline_inspect($1,$2,$3,$4);','SELECT signature_bytes INTO inspect_bytes FROM public.offline_expected_signed_attestation WHERE binding_id=$1;')
    def test_no_caller_selected_decision(self):self.reject('d.decision_id=header_record.decision_id','true')
    def test_no_fake_success(self):self.reject("THEN 'EXACT'","THEN 'SUCCESS'")
    def test_no_civil_timezone_conversion(self):self.reject("decision_record.provider_revision_local-TIMESTAMP '1970-01-01 00:00:00'","decision_record.provider_revision_local AT TIME ZONE 'UTC'-TIMESTAMP '1970-01-01 00:00:00'")

if __name__=='__main__':unittest.main()
