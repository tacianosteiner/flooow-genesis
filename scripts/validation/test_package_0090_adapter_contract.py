"""Negative independent adapter oracle tests, no generator imports."""
import unittest
import package_0090_adapter_review as audit


class AdapterContractTests(unittest.TestCase):
    def test_actual_normative_source(self):
        result=audit.review()
        self.assertEqual(result['public_statement_contracts'],'18/18')
        self.assertEqual(result['direct_legacy_service_call_count'],0)

    def test_wrong_name_parameter_order_slot_and_type_rejected(self):
        original=(audit.SOURCE/'GovernedCall.kt').read_text()
        for old,new in [('offline_begin_grant','offline_begin_permission_grant'),
                        ('verified_envelope pg_catalog.bytea','envelope pg_catalog.bytea'),
                        ('GovernedSlot.VERIFIER','GovernedSlot.ISSUER'),
                        ('expected_generation pg_catalog.int8','expected_generation pg_catalog.int4'),
                        ('binding_id pg_catalog.uuid,plan_fingerprint pg_catalog.bytea','plan_fingerprint pg_catalog.bytea,binding_id pg_catalog.uuid')]:
            with self.subTest(old=old),self.assertRaises(ValueError):
                audit.review({'GovernedCall.kt':original.replace(old,new,1)})

    def test_legacy_dependency_and_connection_escape_rejected(self):
        original=(audit.SOURCE/'GovernedJdbc.kt').read_text()
        for candidate in (original+'\nval sql = "SELECT public.s2a_v042_apply_attested_decision()"',
                          original.replace('"verified_decision_request" to envelope','"verified_decision_request" to byteArrayOf()'),
                          original.replace('check(decisionActive && prepared)','check(true)')):
            with self.assertRaises(ValueError):
                audit.review({'GovernedJdbc.kt':candidate})


if __name__=='__main__':unittest.main()
