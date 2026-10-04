"""Adversarial exact V bridge/ACL source review. No database connection."""
import unittest
import package_0090_source_gate as gate


class VBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig')
        cls.spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')
    def reject(self,source):
        with self.assertRaises(ValueError):gate.prerequisite_checks(source,self.spec)
    def test_exact_bridge_and_unchanged_column_grants(self):
        report=gate.prerequisite_checks(self.source,self.spec)
        self.assertEqual(report['exact_column_grants'],1040)
        self.assertFalse(report['a_direct_native_access'])
        self.assertFalse(report['a_private_crypto_usage'])
    def test_a_native_execute_rejected(self):
        self.reject(self.source+'\nGRANT EXECUTE ON FUNCTION offline_crypto.canonical_spki_ed25519_verify(pg_catalog.bytea,pg_catalog.bytea,pg_catalog.bytea) TO flooow_offline_audit_owner;')
    def test_private_schema_to_a_rejected(self):
        self.reject(self.source+'\nGRANT USAGE ON SCHEMA offline_crypto TO flooow_offline_audit_owner;')
    def test_service_or_public_bridge_execute_rejected(self):
        for recipient in ('PUBLIC','unlisted_service_login'):
            self.reject(self.source+'\nGRANT EXECUTE ON FUNCTION public.offline_internal_canonical_spki_ed25519_verify(pg_catalog.bytea,pg_catalog.bytea,pg_catalog.bytea) TO '+recipient+';')
    def test_bridge_argument_substitution_rejected(self):
        self.reject(self.source.replace('canonical_spki_ed25519_verify($1,$2,$3)','canonical_spki_ed25519_verify($1,$1,$3)'))
    def test_invoker_or_mutable_search_path_rejected(self):
        self.reject(self.source.replace('LANGUAGE plpgsql IMMUTABLE STRICT PARALLEL SAFE SECURITY DEFINER','LANGUAGE plpgsql IMMUTABLE STRICT PARALLEL SAFE SECURITY INVOKER'))
        self.reject(self.source.replace('AS $offline_v_ed25519$','AS $offline_v_ed25519$',1).replace('SET search_path=pg_catalog,pg_temp\nAS $offline_v_ed25519$','SET search_path=public,pg_temp\nAS $offline_v_ed25519$'))
    def test_native_precondition_missing_rejected(self):
        self.reject(self.source.replace("AND p.probin='$libdir/flooow_offline_mac32' AND p.prosrc='canonical_spki_ed25519_verify'",'AND true'))
    def test_operational_errors_must_not_be_caught_as_true(self):
        self.reject(self.source.replace('    RETURN offline_crypto.canonical_spki_ed25519_verify($1,$2,$3);','    RETURN offline_crypto.canonical_spki_ed25519_verify($1,$2,$3);\nEXCEPTION WHEN OTHERS THEN RETURN true;'))


if __name__=='__main__':unittest.main()
