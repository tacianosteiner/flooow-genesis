import unittest
import package_0090_source_gate as gate
import build_package_0090_executor_control_source as control
import build_package_0090_decision_source as decision
from package_0090_verification_source import check
from package_0090_mutation_isolated_review import review as isolated_review

class ExecutorSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(gate.ROOT/gate.V043).read_text()
        cls.spec=(gate.ROOT/gate.SPEC).read_text()
        cls.columns=gate.expected_column_grants(cls.spec)

    def review(self,source,composition):
        statements,_=gate.parse(source)
        for stmt in statements:
            fn=stmt.get('CreateFunctionStmt')
            if fn and fn['funcname'][-1]['String']['sval'] in composition.WRAPPERS.values():check(fn,self.columns,source,composition=composition)

    def test_six_exact_executor_signatures(self):
        self.review(self.source,control);self.review(self.source,decision)

    def test_no_original_input_or_native_access_in_e(self):
        generated=control.build(self.source,self.spec)+decision.build(self.source,self.spec)
        for forbidden in ['offline_expected_signed_attestation','offline_internal_matches_original_signed_attestation','offline_internal_canonical_spki_ed25519_verify','offline_crypto.','SELECT d.*']:
            self.assertNotIn(forbidden,generated)

    def test_control_fencing_delivery_and_lineage_tampering_denied(self):
        generated=control.build(self.source,self.spec)
        for old in ['slot_number=3',"execution_record.state<>'OWNED'",'pointer_record.generation<>$5','receipt_key_version<=0',"delivery_record.state NOT IN ('CREATED_NOT_DELIVERABLE','DELIVERY_ATTEMPTED')",'fresh_outcome<>\'APPLIED\'',"lineage_receipt.receipt_id IS DISTINCT FROM delivery_record.fresh_applied_receipt_id",'admission_record.authorization_fingerprint IS DISTINCT FROM authorization_fingerprint']:
            with self.subTest(old=old):
                self.assertIn(old,generated)
                with self.assertRaises(ValueError):self.review(self.source.replace(generated,generated.replace(old,'false')),control)

    def test_private_derivation_original_snapshot_and_completion_tampering_denied(self):
        generated=decision.build(self.source,self.spec)
        for old in ['request_supersedes_decision_id IS NOT NULL','semantic_count<>1','evidence_record.page_complete IS NOT TRUE','preparation_digest IS DISTINCT FROM','snapshot.result_accepted_proof_fingerprint IS DISTINCT FROM verified_result_accepted_proof_fingerprint',"durable_state='CONSUMED'","state='EFFECTS_COMPLETE'","state='RELEASED'","state='REQUIRED'"]:
            with self.subTest(old=old):
                self.assertIn(old,generated)
                replacement={"durable_state='CONSUMED'":"durable_state='ISSUED'","state='EFFECTS_COMPLETE'":"state='EFFECTS_IN_PROGRESS'","state='RELEASED'":"state='OWNED'","state='REQUIRED'":"state='NOT_STARTED'",'preparation_digest IS DISTINCT FROM':'preparation_digest IS NOT DISTINCT FROM'}.get(old,'false')
                with self.assertRaises(ValueError):self.review(self.source.replace(generated,generated.replace(old,replacement)),decision)

    def test_actual_isolated_mutation_bodies(self):
        self.assertEqual(isolated_review()['status'],'PASS_ACTUAL_S07_S18_WITH_EXPLICIT_STUB_DEPENDENCIES')

if __name__=='__main__':unittest.main()
