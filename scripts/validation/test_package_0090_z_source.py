"""Offline negative checks for Z privilege, identity, output and lock boundaries."""
import unittest
import package_0090_source_gate as gate


class ZSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (gate.ROOT / gate.V043).read_text(encoding='utf-8-sig')
        cls.spec = (gate.ROOT / gate.SPEC).read_text(encoding='utf-8-sig')

    def reject_z(self, before, after):
        prefix, body = self.source.split('AS $offline_z$',1)
        self.assertIn(before, body)
        with self.assertRaises(ValueError):
            gate.prerequisite_checks(prefix+'AS $offline_z$'+body.replace(before,after,1), self.spec)

    def test_current_z_exact_scope(self):
        result = gate.prerequisite_checks(self.source,self.spec)
        self.assertEqual(result['internal_z_source'],'BOUNDED_STATIC_PASS_NOT_RUNTIME_PROOF')

    def test_private_verifier_cannot_be_output(self):
        self.reject_z('pg_catalog.count(*) BETWEEN 1 AND 3 AND pg_catalog.bool_and(x.intent_ok) IS TRUE', 'c.secret_verifier')

    def test_unapproved_private_read(self):
        self.reject_z('c.secret_verifier,o.grant_id', 'c.credential_kind,o.grant_id')

    def test_no_mutation(self):
        self.reject_z('    RETURN QUERY', '    DELETE FROM public.command_principal;\n    RETURN QUERY')

    def test_no_row_locks(self):
        self.reject_z('AND o.decided_at=g.decided_at))', 'AND o.decided_at=g.decided_at)) FOR UPDATE')

    def test_no_wrong_slot(self):
        self.reject_z('slot_number=4 AND slot_name <> SESSION_USER', 'slot_number=3 AND slot_name <> SESSION_USER')

    def test_cannot_drop_credential_scope(self):
        self.reject_z('c.principal_id=header_record.principal_id', 'TRUE')

    def test_cannot_drop_grant_scope(self):
        self.reject_z('g.principal_id=header_record.principal_id', 'TRUE')

    def test_cannot_replace_policy_with_setting(self):
        self.reject_z('pg_catalog.clock_timestamp()', "pg_catalog.current_setting('app.ttl')")

    def test_no_additional_execute_recipient(self):
        with self.assertRaises(ValueError):
            gate.prerequisite_checks(self.source+'\nGRANT EXECUTE ON FUNCTION public.offline_internal_verify_authority_intent(pg_catalog.uuid,pg_catalog.bytea,pg_catalog.uuid,pg_catalog.text) TO flooow_offline_execution_owner;',self.spec)


if __name__ == '__main__':
    unittest.main()
